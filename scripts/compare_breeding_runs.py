"""Compare two completed synthetic batches that differ only in breeding rule."""

import argparse
import json
from pathlib import Path

from simulation.experiments import aggregate
from simulation.model import DEFAULT_BREEDING_RULE, REPO, summary
from validators.results_checks import build_evaluation

COMMON = ('format_version', 'purpose', 'historical_validation', 'seed', 'seed_rule',
          'trials_per_cell', 'duration_months', 'python_version', 'code_sha256',
          'model_conventions', 'aggregation_conventions', 'settlement_rule')


def _read(path):
    def reject_constant(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject_constant)


def _artifact(folder, relative):
    path = Path(relative)
    target = (folder / path).resolve()
    if path.is_absolute() or '..' in path.parts or not target.is_relative_to(folder.resolve()):
        raise ValueError('Trial artifact path must stay inside its batch folder')
    return target


def _load(path, rule, root):
    path = Path(path)
    batch = _read(path)
    if not isinstance(batch, dict):
        raise ValueError('Batch must be a JSON object')
    if any(field not in batch for field in COMMON):
        raise ValueError('Batch is missing required comparison metadata')
    if (batch['format_version'] != 'preview-batch-1' or batch.get('status') != 'completed'
            or batch['purpose'] != 'synthetic_preview'
            or batch['historical_validation'] != 'not_assessed'):
        raise ValueError('Expected a completed synthetic preview batch, with history not assessed')
    if batch.get('breeding_rule') != rule:
        raise ValueError(f'Wrong breeding rule: expected {rule}')
    planned = batch['trials_per_cell']
    if type(planned) is not int or planned < 1:
        raise ValueError('Trials per cell must be a positive integer')
    if not isinstance(batch.get('cells'), list) or not batch['cells']:
        raise ValueError('Batch has no cells')
    cells = {}
    for cell in batch['cells']:
        if not isinstance(cell, dict):
            raise ValueError('Cell must be a JSON object')
        name = cell['name']
        if not isinstance(name, str) or not name or name in cells:
            raise ValueError('Cell name is missing or duplicated')
        if (cell.get('status') != 'completed' or cell.get('planned_trials') != planned
                or not isinstance(cell.get('trials'), list) or len(cell['trials']) != planned):
            raise ValueError(f'Incomplete cell: {name}')
        records, configs = [], []
        for index, record in enumerate(cell['trials']):
            if not isinstance(record, dict):
                raise ValueError('Trial must be a JSON object')
            if record.get('status') != 'completed' or record.get('trial') != index:
                raise ValueError(f'Incomplete or out-of-order trial in {name}')
            folder = _artifact(path.parent, record['artifacts'])
            config, results, saved = (_read(folder / f'{n}.json')
                                      for n in ('input', 'results', 'summary'))
            if not isinstance(config, dict) or not isinstance(results, dict):
                raise ValueError('Input and results must be JSON objects')
            if (config.get('breeding_rule', DEFAULT_BREEDING_RULE) != rule
                    or results.get('data_kind') != 'simulation'):
                raise ValueError(f'Trial has wrong breeding rule or is not a simulation: {name}')
            evaluation = build_evaluation(config, results, root)
            if evaluation['status'] != 'pass':
                raise ValueError(f'Trial failed artifact checks in {name}: '
                                 + ', '.join(issue['code'] for issue in evaluation['issues']))
            expected = summary(results)
            if saved != expected or any(record.get(k) != v for k, v in expected.items()):
                raise ValueError(f'Summary differs from actual results in {name}')
            if record.get('seed') != config['seed']:
                raise ValueError(f'Trial seed differs from its manifest in {name}')
            if (config['duration_months'] != batch['duration_months']
                    or config.get('settlement_rule') != batch['settlement_rule']
                    or config['food_rabbits_per_ha'] != cell['food_rabbits_per_ha']
                    or any(p['area_km2'] != cell['area_km2_per_patch'] for p in config['patches'])):
                raise ValueError(f'Trial settings differ from their batch/cell in {name}')
            records.append(dict(expected, status='completed'))
            comparable = {k: v for k, v in config.items()
                          if k not in ('run_id', 'schema_version', 'breeding_rule')}
            configs.append(comparable)
        # Recompute the displayed statistics from the checked artifacts, never model text.
        stats = aggregate(records)
        if cell.get('statistics') != stats:
            raise ValueError(f'Saved statistics differ from actual trial results in {name}')
        cells[name] = dict(food=cell['food_rabbits_per_ha'], area=cell['area_km2_per_patch'],
                           configs=configs, statistics=stats)
    return batch, cells


def compare_batches(threshold_path, linear_path, *, root=REPO):
    """Reject mismatched runs before computing a descriptive side-by-side report."""
    threshold, first = _load(threshold_path, DEFAULT_BREEDING_RULE, root)
    linear, second = _load(linear_path, 'linear_food_sensitivity', root)
    for field in COMMON:
        if threshold[field] != linear[field]:
            raise ValueError(f'Batches differ in {field}')
    if first.keys() != second.keys():
        raise ValueError('Batches contain different cells')
    cells = []
    for name, a in first.items():
        b = second[name]
        if a['food'] != b['food'] or a['area'] != b['area'] or a['configs'] != b['configs']:
            raise ValueError(f'Inputs or trial seeds differ beyond breeding rule in {name}')
        cells.append(dict(name=name, food=a['food'], area=a['area'],
                          threshold=a['statistics'], linear=b['statistics']))
    return dict(seed=threshold['seed'], trials_per_cell=threshold['trials_per_cell'],
                duration_months=threshold['duration_months'],
                historical_validation='not_assessed', cells=cells)


def render_markdown(comparison):
    def cell(stats):
        low, high = stats['persistence_wilson_95']
        month = stats['extinction_month_median']
        time = 'no extinctions observed' if month is None else f'{month:g} months (extinct trials only)'
        return (f"{stats['persistence_share']:.1%} (95% interval {low:.1%}–{high:.1%}); "
                f"median population {stats['final_population_median']:g}; "
                f"extinction share {stats['extinction_share']:.1%}; median extinction time: {time}")

    lines = ['# Breeding rule comparison', '',
             'Synthetic preview comparison of two assumed breeding rules. Historical validation: **not assessed**.',
             'These results do not establish which rule describes real lynx.', '',
             f"Seed: {comparison['seed']}; trials per cell: {comparison['trials_per_cell']}; months: {comparison['duration_months']}.", '',
             'Persistence means a settled breeding-age female and eligible male share a patch at the endpoint.',
             'Intervals describe each persistence share; they are not a statistical test of the difference.', '',
             '| Food (rabbits/ha), area per patch | Sudden cutoff | Gradual rise | Difference in persistence |',
             '|---|---|---|---|']
    for row in comparison['cells']:
        difference = 100 * (row['linear']['persistence_share'] - row['threshold']['persistence_share'])
        lines.append(f"| {row['food']:g}, {row['area']:g} km² | {cell(row['threshold'])} | "
                     f"{cell(row['linear'])} | {difference:+.1f} percentage points (gradual minus cutoff) |")
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threshold', type=Path, required=True)
    parser.add_argument('--linear', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=REPO, help='research files used for the batches')
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise FileExistsError('Output already exists; choose a new file')
        report = compare_batches(args.threshold, args.linear, root=args.root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(render_markdown(report))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Breeding comparison failed: {exc}')
        return 1
    print(f'Comparison saved to {args.output}. Historical validation: not assessed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
