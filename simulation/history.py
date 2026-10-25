"""History test: does the model grow the 2002 start near the later counts?

This implements `docs/history-test.md` and `docs/history-test-code.md`.  The tolerances,
the seed rule, and the stopping point of the calibration are fixed in code, so a run
cannot quietly change them.  A passing run is weak evidence:  three counts are all we hold.
"""

import argparse
import dataclasses
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

from simulation.model import Lynx, REPO, advance, check_states, load_parameters, preview_config

# Counts from data/history/counts.csv (Andujar-Cardena).
START_TOTAL = 53        # 2002, individuals
START_ADULTS = 25       # 2002, adults
OBSERVED_GROWTH = 1.17  # (190 / 53) ^ (1 / 8) = 1.173 from 2002 to 2010
HELDOUT_COUNT = 214     # 2011, all lynx; never used in calibration

# Tolerances, set before any run and never changed after the 2011 result.
GROWTH_BOUNDS = (1.12, 1.22)    # median growth within 0.05 of 1.17
COUNT_BOUNDS = (192.6, 235.4)   # median 2011 count within 10% of 214

CALIBRATION_MONTHS = 96  # month 0 = 2002 census, month 96 = 2010 census
HELDOUT_MONTHS = 108     # month 108 = 2011 census
YEARS = CALIBRATION_MONTHS // 12

START_MONTH = 12         # month 0 is a December:  census at the end of the year (assumption)
FOOD = 4.6               # rabbits per hectare; any value at or above the spring threshold gives the same run
MORTALITY_RANGE = (0.10, 0.50)
AREAS = (750, 500, 1000)  # total usable km2; the first is the main run (decided 2026-10-24)
CALIBRATION_TRIALS = 100
HELDOUT_TRIALS = 500
HELDOUT_CELL = 'heldout'


def trial_seed(run_seed, cell, trial):
    """One documented rule:  the first 8 bytes of SHA-256 of 'run_seed|cell|trial', as an integer."""
    digest = hashlib.sha256(f'{run_seed}|{cell}|{trial}'.encode()).digest()
    return int.from_bytes(digest[:8], 'big')


def history_start(rng, p, patch_ids):
    """The 53-animal start:  25 adults and 28 non-adults, every draw from `rng`.

    Adults:  whole-month ages uniform from the breeding minimum to the breeding maximum,
    sex 1 : 1 (12 or 13 females, decided by the seed), settled females.
    Non-adults:  whole-month ages uniform from 0 to the breeding minimum minus 1, sex by
    the cub ratio of the table, unsettled.  Animals alternate between the two patches.
    """
    females = START_ADULTS // 2 + rng.randint(0, START_ADULTS % 2)
    sexes = ['female'] * females + ['male'] * (START_ADULTS - females)
    animals = []
    for sex in sexes:
        animals.append(Lynx(f'lynx-{len(animals) + 1:06d}', sex,
                            rng.randint(p.breeding_min, p.breeding_max),
                            patch_ids[len(animals) % 2], settled=sex == 'female'))
    for _ in range(START_TOTAL - START_ADULTS):
        sex = 'female' if rng.random() < p.female_probability else 'male'
        animals.append(Lynx(f'lynx-{len(animals) + 1:06d}', sex,
                            rng.randint(0, p.breeding_min - 1),
                            patch_ids[len(animals) % 2]))
    return animals


def history_config(area_km2, root=REPO):
    """The simulator's synthetic input, with two equal patches that together hold `area_km2`."""
    config = preview_config(seed=0, months=HELDOUT_MONTHS, food=FOOD, area=area_km2 / 2, root=root)
    config['start_month'] = START_MONTH
    return config


def run_trial(p, config, seed, months):
    """Population of every living animal at months 0 to `months`, from one seeded run."""
    rng = random.Random(seed)
    patch_ids = [patch['id'] for patch in config['patches']]
    capacities = {patch['id']: math.floor(patch['area_km2'] / p.home_range)
                  for patch in config['patches']}
    animals = history_start(rng, p, patch_ids)
    check_states(animals, capacities)
    populations = [len(animals)]
    for month in range(1, months + 1):
        populations.append(advance(animals, config, p, rng, month, capacities)['population'])
    return populations


def growth(populations):
    """Annual growth from 2002 to 2010:  (N at month 96 / N at month 0) ^ (1 / 8);  0 if extinct."""
    return (populations[CALIBRATION_MONTHS] / populations[0]) ** (1 / YEARS)


def mortality_grid(step=0.01):
    low, high = MORTALITY_RANGE
    return [round(low + i * step, 6) for i in range(int(round((high - low) / step)) + 1)]


def percentile(values, share):
    ordered = sorted(values)
    position = share * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def spread(values):
    return dict(median=statistics.median(values), p10=percentile(values, 0.1),
                p90=percentile(values, 0.9))


def calibrate(p, config, run_seed, trials=CALIBRATION_TRIALS, grid=None):
    """Change only post-dispersal annual mortality; use 2002 to 2010 only (96 months).

    Chooses the mortality whose median growth is closest to 1.17 (ties go to the lower one).
    The run stops at month 96, so the 2011 count is never computed here.
    """
    rows = []
    for mortality in (grid if grid is not None else mortality_grid()):
        trial_p = dataclasses.replace(p, annual_mortality=mortality)
        cell = f'calibration-m{mortality:.4f}'
        values = [growth(run_trial(trial_p, config, trial_seed(run_seed, cell, t), CALIBRATION_MONTHS))
                  for t in range(trials)]
        rows.append(dict(mortality=mortality, median_growth=statistics.median(values)))
    best = min(rows, key=lambda r: (abs(r['median_growth'] - OBSERVED_GROWTH), r['mortality']))
    return dict(trials=trials, rows=rows, chosen_mortality=best['mortality'],
                chosen_median_growth=best['median_growth'],
                within_tolerance=GROWTH_BOUNDS[0] <= best['median_growth'] <= GROWTH_BOUNDS[1])


def heldout(p, config, run_seed, mortality, trials=HELDOUT_TRIALS):
    """One frozen batch through month 108 at the calibrated mortality; nothing is retuned."""
    frozen = dataclasses.replace(p, annual_mortality=mortality)
    runs = [run_trial(frozen, config, trial_seed(run_seed, HELDOUT_CELL, t), HELDOUT_MONTHS)
            for t in range(trials)]
    counts = [run[HELDOUT_MONTHS] for run in runs]
    return dict(trials=trials, mortality=mortality,
                growth=spread([growth(run) for run in runs]), count_2011=spread(counts),
                extinct_share=sum(count == 0 for count in counts) / trials)


def verdict(median_growth, median_count):
    """Pass only if both medians lie inside the bounds (inclusive)."""
    growth_ok = GROWTH_BOUNDS[0] <= median_growth <= GROWTH_BOUNDS[1]
    count_ok = COUNT_BOUNDS[0] <= median_count <= COUNT_BOUNDS[1]
    return dict(growth_within_bounds=growth_ok, count_2011_within_bounds=count_ok,
                result='pass' if growth_ok and count_ok else 'fail')


REPORT_MUST_SAY = [
    'Three counts (2002, 2010, 2011) are all we hold, so a pass is weak evidence.',
    'Donana parameters are applied to Andujar-Cardena (a transfer assumption).',
    'The starting population is an assumption except the two counts:  12 or 13 adult females, '
    'adult ages 36 to 108 months, non-adult ages 0 to 35 months, cub sex ratio of the table.',
    'The census date is assumed to be the end of the year (month 0 is a December).',
    'The usable area is an assumption (750 km2 for the main run); the verdict uses the main run only.',
]


def run_protocol(output, run_seed, areas=AREAS, calibration_trials=CALIBRATION_TRIALS,
                 heldout_trials=HELDOUT_TRIALS, step=0.01, root=REPO):
    """Calibrate and then run the held-out batch at each area; write the report to a new directory."""
    output = Path(output)
    if output.exists():
        raise ValueError('Output directory already exists; use a new directory')
    first = history_config(areas[0], root)
    p = load_parameters(first, root)
    results = []
    for area in areas:
        config = first if area == areas[0] else history_config(area, root)
        calibration = calibrate(p, config, run_seed, calibration_trials, mortality_grid(step))
        batch = heldout(p, config, run_seed, calibration['chosen_mortality'], heldout_trials)
        results.append(dict(total_area_km2=area, main_run=area == areas[0],
                            calibration=calibration, heldout=batch))
    main = results[0]['heldout']
    report = dict(run_seed=run_seed, bounds=dict(growth=GROWTH_BOUNDS, count_2011=COUNT_BOUNDS),
                  parameters_sha256=first['parameters_sha256'], sources_sha256=first['sources_sha256'],
                  verdict=verdict(main['growth']['median'], main['count_2011']['median']),
                  main_area_km2=areas[0], areas=results, must_say=REPORT_MUST_SAY,
                  historical_validation='weak evidence only; see must_say')
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-seed', type=int, required=True,
                        help='fixed and written down before the first run; every trial seed comes from it')
    parser.add_argument('--areas', type=float, nargs='+', default=list(AREAS),
                        help='total usable km2; the first is the main run')
    parser.add_argument('--calibration-trials', type=int, default=CALIBRATION_TRIALS)
    parser.add_argument('--heldout-trials', type=int, default=HELDOUT_TRIALS)
    parser.add_argument('--mortality-step', type=float, default=0.01)
    parser.add_argument('--output', type=Path, required=True, help='new output directory; never overwritten')
    args = parser.parse_args(argv)
    try:
        report = run_protocol(args.output, args.run_seed, tuple(args.areas), args.calibration_trials,
                              args.heldout_trials, args.mortality_step)
    except (OSError, ValueError) as exc:
        print(f'History test failed: {exc}')
        return 1
    main_run = report['areas'][0]
    print(f"History test saved to {args.output}.  Main run {report['main_area_km2']} km2:  "
          f"calibrated mortality {main_run['calibration']['chosen_mortality']:.2f}, "
          f"median growth {main_run['heldout']['growth']['median']:.3f}, "
          f"median 2011 count {main_run['heldout']['count_2011']['median']:.1f}, "
          f"verdict {report['verdict']['result']}.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
