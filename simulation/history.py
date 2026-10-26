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

from simulation.model import Lynx, REPO, advance, breeding_age, check_states, load_parameters, preview_config
from validators.evidence_gate import check_repository

# Counts from data/history/counts.csv (Andujar-Cardena).
START_TOTAL = 53        # 2002, individuals
START_ADULTS = 25       # 2002, adults
OBSERVED_GROWTH = 1.17  # (190 / 53) ^ (1 / 8) = 1.173 from 2002 to 2010
HELDOUT_COUNT = 202     # 2011, individuals (official series, the issuer's 2011 and 2016 reports); never used in calibration
BESIDE_COUNT = 214      # 2011, Cat Specialist Group page; reported beside the verdict, never used for pass or fail

# Tolerances, set before any run and never changed after the 2011 result.
GROWTH_BOUNDS = (1.12, 1.22)    # median growth within 0.05 of 1.17
COUNT_BOUNDS = (181.8, 222.2)   # median 2011 count within 10% of 202 (Valerie, 2026-10-25, source quality)
BESIDE_BOUNDS = (192.6, 235.4)  # within 10% of 214; reported only

# Second observable (proposed in #62):  territorial females, reported beside the verdict for the main run only.
# It has no tolerance and no pass or fail.  Counts from data/history/counts.csv ("territorial females (official series)").
CENSUS_TERRITORIAL_FEMALES = {2010: 43, 2011: 51}

CALIBRATION_MONTHS = 96  # month 0 = 2002 census, month 96 = 2010 census
HELDOUT_MONTHS = 108     # month 108 = 2011 census
YEARS = CALIBRATION_MONTHS // 12

START_MONTH = 12         # month 0 is a December:  census at the end of the year (assumption)
FOOD = 4.6               # rabbits per hectare; any value at or above the spring threshold gives the same run
MORTALITY_RANGE = (0.10, 0.50)
# Arms of the run:  (total usable km2, female home range in km2 or None for the table's value).  The first is the
# main run and the only one that decides the verdict (750 km2, decided 2026-10-24); the 264 km2 comparisons at
# home ranges of 6.1 and 10 km2 follow the plan in #45 (Valerie accepted it on 2026-10-25).
ARMS = ((750, None), (264, 6.1), (264, 10.0))
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


def territory_capacities(config, p):
    """Female territories per patch:  usable area divided by the female home range, rounded down."""
    return {patch['id']: math.floor(patch['area_km2'] / p.home_range) for patch in config['patches']}


def parse_arm(text):
    """'750' gives (750.0, None); '264:6.1' gives (264.0, 6.1)."""
    area, separator, home_range = text.partition(':')
    try:
        if separator and not home_range:
            raise ValueError
        values = (float(area), float(home_range) if home_range else None)
    except ValueError:
        raise ValueError(f'cannot read the arm {text!r}; use AREA or AREA:HOME_RANGE') from None
    if (not math.isfinite(values[0]) or values[0] <= 0
            or (values[1] is not None and (not math.isfinite(values[1]) or values[1] <= 0))):
        raise ValueError(f'the arm {text!r} needs a positive area and home range')
    return values


def settled_breeding_females(animals, p):
    """Living females that hold a territory and are of breeding age:  the model's reading of a territorial female."""
    return sum(1 for a in animals if a.sex == 'female' and a.settled and breeding_age(a, p))


def run_trial_detail(p, config, seed, months, observe=(CALIBRATION_MONTHS, HELDOUT_MONTHS)):
    """One seeded run:  the population at months 0 to `months`, and the settled breeding females at `observe`.

    Counting females draws nothing from the random generator, so the run is the same with or without it.
    """
    rng = random.Random(seed)
    patch_ids = [patch['id'] for patch in config['patches']]
    capacities = territory_capacities(config, p)
    animals = history_start(rng, p, patch_ids)
    check_states(animals, capacities)
    populations = [len(animals)]
    settled_females = {}
    for month in range(1, months + 1):
        populations.append(advance(animals, config, p, rng, month, capacities)['population'])
        if month in observe:
            settled_females[month] = settled_breeding_females(animals, p)
    return dict(populations=populations, settled_females=settled_females)


def run_trial(p, config, seed, months):
    """Population of every living animal at months 0 to `months`, from one seeded run."""
    return run_trial_detail(p, config, seed, months, observe=())['populations']


def growth(populations):
    """Annual growth from 2002 to 2010:  (N at month 96 / N at month 0) ^ (1 / 8);  0 if extinct."""
    return (populations[CALIBRATION_MONTHS] / populations[0]) ** (1 / YEARS)


def mortality_grid(step=0.01):
    low, high = MORTALITY_RANGE
    if not math.isfinite(step) or step <= 0 or step > high - low:
        raise ValueError(f'mortality step must be greater than 0 and no larger than {high - low}')
    intervals = (high - low) / step
    nearest = round(intervals)
    if not math.isclose(intervals, nearest, rel_tol=0, abs_tol=1e-9):
        raise ValueError('mortality step must divide the mortality range evenly')
    return [round(low + i * step, 6) for i in range(nearest + 1)]


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
    if trials <= 0:
        raise ValueError('calibration trials must be greater than 0')
    mortality_values = list(grid if grid is not None else mortality_grid())
    if not mortality_values:
        raise ValueError('mortality grid must contain at least one value')
    rows = []
    for mortality in mortality_values:
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
    if trials <= 0:
        raise ValueError('held-out trials must be greater than 0')
    frozen = dataclasses.replace(p, annual_mortality=mortality)
    runs = [run_trial_detail(frozen, config, trial_seed(run_seed, HELDOUT_CELL, t), HELDOUT_MONTHS)
            for t in range(trials)]
    counts = [run['populations'][HELDOUT_MONTHS] for run in runs]
    return dict(trials=trials, mortality=mortality,
                growth=spread([growth(run['populations']) for run in runs]), count_2011=spread(counts),
                extinct_share=sum(count == 0 for count in counts) / trials,
                settled_females_2010=spread([run['settled_females'][CALIBRATION_MONTHS] for run in runs]),
                settled_females_2011=spread([run['settled_females'][HELDOUT_MONTHS] for run in runs]))


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
    'The usable area is an assumption (750 km2 for the main run); the verdict uses the main run only.  '
    'The 264 km2 arms use female home ranges of 6.1 and 10 km2 and are reported beside it.',
    "The 2011 target of 202 is the issuer's own figure (its 2011 and 2016 reports); 214 (Cat Specialist Group) "
    'is reported beside it and never used for pass or fail.',
    'The 2011 count adds one year at the calibrated rate; it is not independent of the calibration.',
    'Territorial females (43 in 2010 and 51 in 2011) are reported beside the verdict for the 750 km2 run only, as the '
    'median number of settled females of breeding age with the 10th and 90th percentiles; there is no tolerance and '
    'no pass or fail, and we do not call it support or failure.  The 264 km2 arms hold fewer territories than the '
    'census counts, so their numbers are marked capacity-limited and are not compared.',
]


def second_observable(results):
    """Territorial females beside the verdict:  report-only; the main run is the only one that is compared."""
    arms = []
    for result in results:
        capacity = result['territories']
        arms.append(dict(total_area_km2=result['total_area_km2'],
                         female_home_range_km2=result['female_home_range_km2'],
                         territories=capacity, main_run=result['main_run'],
                         compared=result['main_run'],
                         capacity_limited={str(year): capacity < count
                                           for year, count in CENSUS_TERRITORIAL_FEMALES.items()},
                         model_2010=result['heldout']['settled_females_2010'],
                         model_2011=result['heldout']['settled_females_2011']))
    return dict(scored=False, tolerance=None,
                definition='living females that hold a territory and are of breeding age, at the census month',
                census={str(year): count for year, count in CENSUS_TERRITORIAL_FEMALES.items()}, arms=arms)


def run_protocol(output, run_seed, arms=ARMS, calibration_trials=CALIBRATION_TRIALS,
                 heldout_trials=HELDOUT_TRIALS, step=0.01, root=REPO):
    """Calibrate and then run the held-out batch at each arm; write the report to a new directory."""
    output = Path(output)
    if output.exists():
        raise ValueError('Output directory already exists; use a new directory')
    if not arms:
        raise ValueError('at least one run arm is required')
    if arms[0] != (750, None):
        raise ValueError('the first arm must be the agreed 750 km2 primary run')
    if calibration_trials <= 0 or heldout_trials <= 0:
        raise ValueError('calibration and held-out trial counts must be greater than 0')
    mortality_grid(step)  # validate the grid before beginning a potentially long run
    for area, home_range in arms:
        if (not math.isfinite(area) or area <= 0
                or (home_range is not None and (not math.isfinite(home_range) or home_range <= 0))):
            raise ValueError('every run arm needs a finite positive area and, when provided, home range')
    first = history_config(arms[0][0], root)
    table = load_parameters(first, root)
    results = []
    for number, (area, home_range) in enumerate(arms):
        p = table if home_range is None else dataclasses.replace(table, home_range=home_range)
        config = first if area == arms[0][0] else history_config(area, root)
        calibration = calibrate(p, config, run_seed, calibration_trials, mortality_grid(step))
        batch = heldout(p, config, run_seed, calibration['chosen_mortality'], heldout_trials)
        results.append(dict(total_area_km2=area, female_home_range_km2=p.home_range, main_run=number == 0,
                            territories=sum(territory_capacities(config, p).values()),
                            calibration=calibration, heldout=batch))
    main = results[0]['heldout']
    beside = dict(count_2011=BESIDE_COUNT, bounds=BESIDE_BOUNDS, used_for_verdict=False,
                  median_within_bounds=BESIDE_BOUNDS[0] <= main['count_2011']['median'] <= BESIDE_BOUNDS[1])
    report = dict(run_seed=run_seed, bounds=dict(growth=GROWTH_BOUNDS, count_2011=COUNT_BOUNDS),
                  parameters_sha256=first['parameters_sha256'], sources_sha256=first['sources_sha256'],
                  verdict=verdict(main['growth']['median'], main['count_2011']['median']),
                  reported_beside=beside, second_observable=second_observable(results),
                  main_area_km2=arms[0][0], areas=results, must_say=REPORT_MUST_SAY,
                  historical_validation='weak evidence only; see must_say')
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-seed', type=int, required=True,
                        help='fixed and written down before the first run; every trial seed comes from it')
    parser.add_argument('--arms', nargs='+', metavar='AREA[:HOME_RANGE]',
                        help='total usable km2 with an optional female home range in km2 (for example 264:6.1); '
                             'the first is the main run (default: 750 264:6.1 264:10)')
    parser.add_argument('--calibration-trials', type=int, default=CALIBRATION_TRIALS)
    parser.add_argument('--heldout-trials', type=int, default=HELDOUT_TRIALS)
    parser.add_argument('--mortality-step', type=float, default=0.01)
    parser.add_argument('--output', type=Path, required=True, help='new output directory; never overwritten')
    args = parser.parse_args(argv)
    # The history test is one held-out run, so it always runs the final gate:  there is no stage option to forget.
    refused, _ = check_repository(REPO, 'final')
    if refused:
        print('History test refused by the evidence gate: ' + '; '.join(refused))
        return 2
    try:
        arms = ARMS if args.arms is None else tuple(parse_arm(text) for text in args.arms)
        report = run_protocol(args.output, args.run_seed, arms, args.calibration_trials,
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
