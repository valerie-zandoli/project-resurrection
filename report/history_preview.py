"""A small development-only 2002–2010 comparison; never run the held-out batch."""
import argparse
import csv
import json
import platform
import statistics
from pathlib import Path

from harness.snapshot import make_snapshot
from simulation import history
from simulation.model import REPO, load_parameters
from validators.evidence_gate import check_repository
from validators.handoff_hashes import file_sha256

PREVIEW_SEED = 20261028  # deliberately differs from the preregistered final seed
TRIALS = 5
MONTHS = 96


def build_preview(output, source_root=REPO):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    snapshot = output / 'snapshot'
    hashes = make_snapshot(source_root, snapshot)
    errors, evidence = check_repository(snapshot, 'pilot')
    if errors:
        raise ValueError('Research evidence check failed: ' + '; '.join(errors))
    config = history.history_config(750, root=snapshot)
    config['duration_months'] = MONTHS
    parameters = load_parameters(config, snapshot)
    # No calibration and no call to heldout/run_history: every trial stops at 2010.
    runs = [history.run_trial_detail(parameters, config,
                history.trial_seed(PREVIEW_SEED, 'development-preview-through-2010', trial),
                MONTHS, observe=())['populations'] for trial in range(TRIALS)]
    counts_path = Path(source_root) / 'data/history/counts.csv'
    with counts_path.open(encoding='utf-8-sig', newline='') as handle:
        counts = {int(row['year']): dict(observed=int(row['count']), source=row['source'])
                  for row in csv.DictReader(handle)
                  if row['population'] == 'Andujar-Cardena' and row['definition'] == 'individuals'
                  and row['year'] in ('2002', '2010')}
    if set(counts) != {2002, 2010}:
        raise ValueError('The preview needs the recorded 2002 and 2010 individual counts.')
    rows = []
    for year, month in [(2002, 0), (2010, MONTHS)]:
        values = [run[month] for run in runs]
        median = statistics.median(values)
        observed = counts[year]['observed']
        rows.append(dict(year=year, observed=observed, simulated_median=median,
                         simulated_min=min(values), simulated_max=max(values),
                         difference=median-observed, difference_percent=100*(median-observed)/observed,
                         source=counts[year]['source'], initialization=year == 2002))
    report = dict(kind='development_history_preview', historical_validation='not_assessed',
                  heldout_run=False, calibrated=False, seed=PREVIEW_SEED, trials=TRIALS,
                  through_year=2010, area_km2=750, food=history.FOOD,
                  annual_mortality=parameters.annual_mortality, rows=rows,
                  observed_growth=(counts[2010]['observed']/counts[2002]['observed'])**(1/8),
                  simulated_growth=statistics.median(history.growth(run) for run in runs),
                  growth_bounds=list(history.GROWTH_BOUNDS), research_sha256=hashes,
                  counts_sha256=file_sha256(counts_path), python_version=platform.python_version(),
                  model_sha256=file_sha256(REPO/'simulation/model.py'),
                  history_code_sha256=file_sha256(REPO/'simulation/history.py'), evidence=evidence)
    (output/'input.json').write_text(json.dumps(config, indent=2)+'\n')
    (output/'trial-populations.json').write_text(json.dumps(runs)+'\n')
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report


def read_panel(path):
    """Expose only an explicitly supplied, development-only report's display fields."""
    if path is None:
        return None
    report = json.loads(Path(path).read_text())
    if (report.get('kind') != 'development_history_preview'
            or report.get('heldout_run') is not False or report.get('calibrated') is not False
            or report.get('through_year') != 2010 or report.get('historical_validation') != 'not_assessed'
            or [row['year'] for row in report.get('rows', [])] != [2002, 2010]):
        raise ValueError('Only an uncalibrated development preview ending in 2010 may be displayed here.')
    keys = ('kind', 'historical_validation', 'heldout_run', 'calibrated', 'seed', 'trials',
            'through_year', 'area_km2', 'food', 'annual_mortality', 'observed_growth',
            'simulated_growth', 'growth_bounds')
    panel = {key: report[key] for key in keys}
    fields = ('year', 'observed', 'simulated_median', 'simulated_min', 'simulated_max',
              'difference', 'difference_percent', 'source', 'initialization')
    panel['rows'] = [{key: row[key] for key in fields} for row in report['rows']]
    json.dumps(panel, allow_nan=False)
    return panel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build_preview(args.output)
    print('Development preview through 2010 only; five uncalibrated trials. Held-out batch not run.')
    for row in report['rows']:
        print(f"{row['year']}: observed {row['observed']}; simulated median {row['simulated_median']}; difference {row['difference']:+g}")


if __name__ == '__main__':
    main()


def read_calibration(path):
    """Read an explicitly selected development-only calibration, never run history."""
    if path is None:
        return None
    report = json.loads(Path(path).read_text())
    if (report.get('kind') != 'development_calibration_only'
            or report.get('heldout_run') is not False or report.get('through_year') != 2010):
        raise ValueError('Only a development calibration ending in 2010 may be displayed.')
    rows = report['rows']
    if not rows or any(not 0.10 <= row['mortality'] <= 0.50 for row in rows):
        raise ValueError('Calibration mortality must remain in the agreed range.')
    chosen = min(rows, key=lambda row: (abs(row['median_growth'] - 1.17), row['mortality']))
    if (chosen['mortality'] != report['chosen_mortality']
            or chosen['median_growth'] != report['chosen_median_growth']
            or type(report['trials']) is not int or report['trials'] < 1):
        raise ValueError('Calibration summary does not match its saved grid.')
    return dict(chosen_mortality=chosen['mortality'], chosen_median_growth=chosen['median_growth'],
                within_tolerance=1.12 <= chosen['median_growth'] <= 1.22,
                settings=len(rows), trials=report['trials'], seed=report['seed'])
