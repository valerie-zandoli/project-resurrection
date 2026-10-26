"""Repeated synthetic previews; proposed conventions remain unapproved."""

import argparse
import copy
import hashlib
import json
import math
import platform
from pathlib import Path
from statistics import median

from simulation.model import REPO, preview_config, simulate, summary

CELLS = tuple((f'food-{food:g}_area-{area}', food, area)
              for food in (1.0, 4.6, 55.0) for area in (50, 100))
SEED_RULE = 'sha256-json-v1:first-8-bytes-big-endian'


def trial_seed(seed, cell, trial):
    """Zero-based trial index; never use Python's process-dependent hash()."""
    payload = json.dumps(['lynx-preview-batch-v1', seed, cell, trial],
                         separators=(',', ':'), ensure_ascii=True).encode('ascii')
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big')


def percentile(values, fraction):
    """Linear interpolation at (n - 1) * fraction, including the endpoints."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def aggregate(records):
    """Only a complete cell can be summarized; failed trials are never dropped."""
    if not records or any(row['status'] != 'completed' for row in records):
        raise ValueError('Only completed trials may be aggregated')
    n = len(records)
    successes = sum(row['persisted'] for row in records)
    proportion = successes / n
    z = 1.959963984540054  # Two-sided standard normal 95% quantile.
    denominator = 1 + z * z / n
    center = (proportion + z * z / (2 * n)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / n + z * z / (4 * n * n)) / denominator
    populations = [row['final_population'] for row in records]
    extinctions = [row['extinction_month'] for row in records
                   if row['extinction_month'] is not None]
    return dict(trials=n, persistence_share=proportion,
                persistence_wilson_95=[max(0.0, center - half), min(1.0, center + half)],
                final_population_median=median(populations),
                final_population_p10=percentile(populations, 0.1),
                final_population_p90=percentile(populations, 0.9),
                extinction_share=len(extinctions) / n,
                extinction_month_median=median(extinctions) if extinctions else None)


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def run_batch(output, seed=42, trials=100, months=120):
    """Save every attempt, stopping the batch at the first failure without retry."""
    if any(type(value) is not int for value in (seed, trials, months)):
        raise ValueError('Seed, trials, and months must be integers')
    if seed < 0 or trials < 1 or months < 1:
        raise ValueError('Seed must be nonnegative; trials and months must be positive')
    # Capture all research identities before the first trial. Later edits fail
    # simulate()'s hash checks rather than becoming a different input mid-batch.
    configs = {name: preview_config(seed, months, food, area) for name, food, area in CELLS}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = dict(format_version='preview-batch-1', status='running',
                  purpose='synthetic_preview', historical_validation='not_assessed',
                  model_conventions='proposed-2026-10-22',
                  aggregation_conventions='proposed-model-conventions-section-4',
                  seed=seed, seed_rule=SEED_RULE, trials_per_cell=trials,
                  duration_months=months, python_version=platform.python_version(),
                  code_sha256={name: hashlib.sha256((REPO / name).read_bytes()).hexdigest()
                               for name in ('simulation/model.py', 'simulation/experiments.py',
                                            'schemas/input.schema.json', 'schemas/results.schema.json')},
                  cells=[dict(name=name, food_rabbits_per_ha=food, area_km2_per_patch=area,
                              planned_trials=trials, status='pending', trials=[], statistics=None)
                         for name, food, area in CELLS])
    manifest = output / 'batch.json'
    identity = dict(configs=configs, code=report['code_sha256'],
                    python=report['python_version'], trials=trials)
    report['batch_id'] = hashlib.sha256(json.dumps(identity, sort_keys=True,
                                                  separators=(',', ':')).encode()).hexdigest()[:24]
    write_json(manifest, report)
    for cell in report['cells']:
        cell['status'] = 'running'
        for trial in range(trials):
            config = copy.deepcopy(configs[cell['name']])
            config.update(seed=trial_seed(seed, cell['name'], trial),
                          run_id=f"preview-{report['batch_id']}-{cell['name']}-{trial:06d}")
            relative = Path(cell['name']) / f'trial-{trial:06d}'
            record = dict(trial=trial, seed=config['seed'], run_id=config['run_id'],
                          artifacts=relative.as_posix(), status='running')
            cell['trials'].append(record)
            # Persist intent before execution: a killed process leaves a visible
            # running attempt, never a falsely complete cell or a missing seed.
            write_json(manifest, report)
            try:
                directory = output / relative
                directory.mkdir(parents=True, exist_ok=False)
                write_json(directory / 'input.json', config)
                result = simulate(config)
                statistics = summary(result)
                write_json(directory / 'results.json', result)
                write_json(directory / 'summary.json', statistics)
                record.update(statistics, status='completed')
            except (Exception, KeyboardInterrupt) as exc:
                record.update(status='failed', error_type=type(exc).__name__, error=str(exc))
                cell['status'] = 'incomplete'
                report['status'] = 'incomplete'
                write_json(manifest, report)
                return report
            write_json(manifest, report)
        cell['statistics'] = aggregate(cell['trials'])
        cell['status'] = 'completed'
        write_json(manifest, report)
    report['status'] = 'completed'
    write_json(manifest, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', required=True,
                        help='acknowledge proposed model and aggregation conventions')
    parser.add_argument('--output', type=Path, required=True, help='new output directory')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--trials', type=int, default=100, help='per cell; preview only, including 500')
    parser.add_argument('--months', type=int, default=120)
    args = parser.parse_args(argv)
    try:
        report = run_batch(args.output, args.seed, args.trials, args.months)
    except (OSError, ValueError) as exc:
        print(f'Batch failed: {exc}')
        return 1
    print(f"Preview batch {report['status']}: {args.output / 'batch.json'}. "
          'Historical validation: not assessed.')
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
