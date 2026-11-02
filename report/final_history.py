"""Read the archived final comparison without running or recalibrating it."""
import json
import math

from simulation.model import REPO

ARCHIVE = REPO / 'examples/final_history_20261102/report.json'


def read_final_history(path=ARCHIVE):
    report = json.loads(path.read_text())
    main, = [arm for arm in report['areas'] if arm['main_run']]
    held = main['heldout']
    checks = {}
    for field, label in [('growth', 'growth_within_bounds'),
                         ('count_2011', 'count_2011_within_bounds')]:
        value = held[field]['median']
        low, high = report['bounds'][field]
        if not all(math.isfinite(v) for v in (value, low, high)) or low > high:
            raise ValueError('Invalid final historical comparison numbers')
        checks[label] = low <= value <= high
    checks['result'] = 'pass' if all(checks.values()) else 'fail'
    if report['verdict'] != checks:
        raise ValueError('Historical verdict does not match saved medians')
    return report
