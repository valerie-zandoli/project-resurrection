"""History test code:  the start, the seed rule, the tolerances, and the one-way protocol."""

import csv
import dataclasses
import json
import random
import statistics

import pytest

from simulation import history
from simulation.history import (CALIBRATION_MONTHS, COUNT_BOUNDS, GROWTH_BOUNDS, HELDOUT_MONTHS,
                                calibrate, growth, heldout, history_config, history_start,
                                main, mortality_grid, percentile, run_protocol, run_trial,
                                trial_seed, verdict)
from simulation.model import REPO, load_parameters


@pytest.fixture(scope='module')
def config():
    return history_config(750)


@pytest.fixture(scope='module')
def params(config):
    return load_parameters(config, REPO)


def census(population, year, definition):
    with (REPO / 'data/history/counts.csv').open(encoding='utf-8-sig', newline='') as handle:
        rows = [r for r in csv.DictReader(handle)
                if r['population'] == population and int(r['year']) == year
                and r['definition'] == definition]
    assert len(rows) == 1
    return float(rows[0]['count'])


def test_constants_match_the_census_file_and_the_accepted_tolerances():
    assert history.START_TOTAL == census('Andujar-Cardena', 2002, 'individuals') == 53
    assert history.START_ADULTS == census('Andujar-Cardena', 2002, 'adults') == 25
    assert history.BESIDE_COUNT == census('Andujar-Cardena', 2011, 'all lynx') == 214
    assert history.HELDOUT_COUNT == 202  # its row reaches counts.csv with #57; read it here after that merges
    observed = (census('Andujar-Cardena', 2010, 'individuals') / 53) ** (1 / 8)
    assert observed == pytest.approx(1.173, abs=0.001)
    assert GROWTH_BOUNDS == (pytest.approx(history.OBSERVED_GROWTH - 0.05), pytest.approx(history.OBSERVED_GROWTH + 0.05))
    assert GROWTH_BOUNDS == (1.12, 1.22)
    assert COUNT_BOUNDS == (pytest.approx(202 * 0.9), pytest.approx(202 * 1.1))
    assert COUNT_BOUNDS == (181.8, 222.2)
    assert history.BESIDE_BOUNDS == (pytest.approx(214 * 0.9), pytest.approx(214 * 1.1))
    assert (CALIBRATION_MONTHS, HELDOUT_MONTHS) == (96, 108)


def test_the_census_is_taken_in_december_so_month_96_is_2010_and_108_is_2011(config):
    assert config['start_month'] == 12
    assert (config['start_month'] - 1 + 96) % 12 + 1 == 12
    assert (config['start_month'] - 1 + 108) % 12 + 1 == 12


def test_the_areas_split_equally_across_two_patches(config):
    assert [patch['area_km2'] for patch in config['patches']] == [375, 375]
    assert [patch['area_km2'] for patch in history_config(500)['patches']] == [250, 250]
    assert history.ARMS[0] == (750, None) and history.ARMS[1:] == ((264, 6.1), (264, 10.0))


def test_territories_follow_the_area_and_the_home_range(params):
    small = history_config(264)
    assert sum(history.territory_capacities(small, dataclasses.replace(params, home_range=6.1)).values()) == 42
    assert sum(history.territory_capacities(small, dataclasses.replace(params, home_range=10.0)).values()) == 26
    assert sum(history.territory_capacities(history_config(750), params).values()) == 74


def test_an_arm_is_an_area_with_or_without_a_home_range():
    assert history.parse_arm('750') == (750.0, None)
    assert history.parse_arm('264:6.1') == (264.0, 6.1)
    for bad in ('', 'x', '264:', '264:y', '0', '-5', '264:0'):
        with pytest.raises(ValueError):
            history.parse_arm(bad)


def test_start_has_53_animals_25_adults_and_28_non_adults(params):
    for seed in range(50):
        animals = history_start(random.Random(seed), params, ['A', 'B'])
        assert len(animals) == 53
        assert len({a.id for a in animals}) == 53
        adults = animals[:25]
        non_adults = animals[25:]
        assert all(params.breeding_min <= a.age_months <= params.breeding_max for a in adults)
        assert all(0 <= a.age_months < params.breeding_min for a in non_adults)
        assert sum(a.sex == 'female' for a in adults) in (12, 13)
        assert all(a.alive for a in animals)
        assert all(a.settled == (a in adults and a.sex == 'female') for a in animals)
        assert {a.patch_id for a in animals} == {'A', 'B'}


def test_start_is_the_same_for_one_seed_and_differs_between_seeds(params):
    first = history_start(random.Random(7), params, ['A', 'B'])
    again = history_start(random.Random(7), params, ['A', 'B'])
    other = history_start(random.Random(8), params, ['A', 'B'])
    assert first == again
    assert first != other


def test_non_adult_sex_follows_the_cub_ratio(params):
    non_adults = [a for seed in range(300)
                  for a in history_start(random.Random(seed), params, ['A', 'B'])[25:]]
    share = sum(a.sex == 'female' for a in non_adults) / len(non_adults)
    assert share == pytest.approx(params.female_probability, abs=0.02)


def test_trial_seed_rule_is_fixed_and_separates_cells_trials_and_run_seeds():
    # A change to the rule changes these numbers on purpose:  edit them only with a reason in the commit.
    assert trial_seed(1, 'heldout', 0) == 16907564237663843682
    assert trial_seed(42, 'calibration-m0.2000', 7) == 9091613605350008076
    assert trial_seed(1, 'heldout', 0) == trial_seed(1, 'heldout', 0)
    assert 0 <= trial_seed(1, 'heldout', 0) < 2 ** 64
    seeds = {trial_seed(run, cell, t) for run in (1, 2) for cell in ('heldout', 'calibration-m0.2000')
             for t in range(500)}
    assert len(seeds) == 2 * 2 * 500


def test_heldout_seeds_never_appear_in_calibration():
    heldout_seeds = {trial_seed(5, 'heldout', t) for t in range(500)}
    calibration_seeds = {trial_seed(5, f'calibration-m{m:.4f}', t)
                         for m in mortality_grid() for t in range(100)}
    assert not heldout_seeds & calibration_seeds


def test_growth_is_the_annual_rate_from_month_0_to_month_96():
    flat = [53] * 109
    assert growth(flat) == pytest.approx(1.0)
    extinct = [53] + [0] * 108
    assert growth(extinct) == 0.0
    observed = [53] + [0] * 95 + [190] + [0] * 12
    assert growth(observed) == pytest.approx((190 / 53) ** (1 / 8))
    assert growth([53] + [0] * 95 + [999, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]) == pytest.approx((999 / 53) ** (1 / 8))


@pytest.mark.parametrize('median_growth, median_count, expected', [
    (1.12, 181.8, 'pass'), (1.22, 222.2, 'pass'), (1.17, 202, 'pass'),
    (1.1199, 202, 'fail'), (1.2201, 202, 'fail'),
    (1.17, 181.79, 'fail'), (1.17, 222.21, 'fail'),
])
def test_verdict_bounds_are_inclusive_and_both_must_hold(median_growth, median_count, expected):
    assert verdict(median_growth, median_count)['result'] == expected


def test_mortality_grid_covers_0_10_to_0_50():
    grid = mortality_grid()
    assert grid[0] == 0.10 and grid[-1] == 0.50 and len(grid) == 41
    assert mortality_grid(0.2) == [0.1, 0.3, 0.5]


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert percentile([1, 2, 3, 4, 5], 0.1) == pytest.approx(1.4)
    assert percentile([1, 2, 3, 4, 5], 0.9) == pytest.approx(4.6)


def test_median_growth_falls_as_mortality_rises_on_the_real_model(params, config):
    # The calibration assumes this.  A development check only:  months 0 to 96, a run seed that no real run uses,
    # and no 2011 count is computed or printed (docs/history-preregistration.md, "What counts as looking").
    def median_growth(mortality):
        trial_p = dataclasses.replace(params, annual_mortality=mortality)
        return statistics.median(
            growth(run_trial(trial_p, config, trial_seed(987654, f'dev-m{mortality}', t), CALIBRATION_MONTHS))
            for t in range(20))

    assert median_growth(0.15) > median_growth(0.35) > median_growth(0.50)


def test_calibration_never_simulates_past_month_96(params, config, monkeypatch):
    months_seen = set()

    def fake(p, cfg, seed, months):
        months_seen.add(months)
        return [53] * (months + 1)

    monkeypatch.setattr(history, 'run_trial', fake)
    calibrate(params, config, 1, trials=2, grid=[0.2, 0.3])
    assert months_seen == {96}


def test_calibration_picks_the_mortality_with_growth_closest_to_1_17(params, config, monkeypatch):
    # Fake world:  growth is 1.17 at mortality 0.30 and falls by 0.01 for each 0.01 above or below it.
    def fake(p, cfg, seed, months):
        rate = 1.17 - abs(p.annual_mortality - 0.30)
        return [53] + [0] * 95 + [53 * rate ** 8] + [0] * (months - 96)

    monkeypatch.setattr(history, 'run_trial', fake)
    result = calibrate(params, config, 1, trials=3, grid=mortality_grid(0.05))
    assert result['chosen_mortality'] == pytest.approx(0.30)
    assert result['within_tolerance'] is True


def test_calibration_ties_go_to_the_lower_mortality(params, config, monkeypatch):
    def fake(p, cfg, seed, months):
        return [53] + [0] * 95 + [53 * 1.17 ** 8] + [0] * (months - 96)

    monkeypatch.setattr(history, 'run_trial', fake)
    assert calibrate(params, config, 1, trials=2, grid=[0.4, 0.2, 0.3])['chosen_mortality'] == 0.2


def test_calibration_reports_when_no_mortality_reaches_the_tolerance(params, config, monkeypatch):
    def fake(p, cfg, seed, months):
        return [53] + [0] * 95 + [53 * 0.9 ** 8] + [0] * (months - 96)

    monkeypatch.setattr(history, 'run_trial', fake)
    assert calibrate(params, config, 1, trials=2, grid=[0.2, 0.3])['within_tolerance'] is False


def test_heldout_uses_the_frozen_mortality_and_only_heldout_seeds(params, config, monkeypatch):
    seen = []

    def fake(p, cfg, seed, months):
        seen.append((p.annual_mortality, seed, months))
        return [53] * (months + 1)

    monkeypatch.setattr(history, 'run_trial', fake)
    batch = heldout(params, config, 9, 0.2, trials=7)
    assert batch['mortality'] == 0.2
    assert {m for m, _, _ in seen} == {0.2}
    assert {mo for _, _, mo in seen} == {108}
    assert [s for _, s, _ in seen] == [trial_seed(9, 'heldout', t) for t in range(7)]


def test_real_trial_is_deterministic_and_has_one_population_per_month(params, config):
    first = run_trial(params, config, 123, HELDOUT_MONTHS)
    assert first == run_trial(params, config, 123, HELDOUT_MONTHS)
    assert len(first) == 109 and first[0] == 53
    assert first != run_trial(params, config, 124, HELDOUT_MONTHS)


def test_protocol_runs_end_to_end_and_writes_a_complete_report(tmp_path):
    out = tmp_path / 'run'
    report = run_protocol(out, 99, arms=((750, None), (264, 6.1)), calibration_trials=2, heldout_trials=3, step=0.2)
    saved = json.loads((out / 'report.json').read_text())
    assert saved == json.loads(json.dumps(report))
    assert [a['total_area_km2'] for a in saved['areas']] == [750, 264]
    assert [a['female_home_range_km2'] for a in saved['areas']] == [10.0, 6.1]
    assert [a['territories'] for a in saved['areas']] == [74, 42]
    assert saved['areas'][0]['main_run'] and not saved['areas'][1]['main_run']
    main_run = saved['areas'][0]
    assert main_run['heldout']['trials'] == 3 and main_run['calibration']['trials'] == 2
    assert main_run['heldout']['mortality'] == main_run['calibration']['chosen_mortality']
    assert {'median', 'p10', 'p90'} <= set(main_run['heldout']['count_2011'])
    assert 0 <= main_run['heldout']['extinct_share'] <= 1
    # The verdict comes from the main run only.
    assert saved['verdict'] == verdict(main_run['heldout']['growth']['median'],
                                       main_run['heldout']['count_2011']['median'])
    assert saved['bounds'] == {'growth': [1.12, 1.22], 'count_2011': [181.8, 222.2]}
    assert len(saved['must_say']) == 7
    beside = saved['reported_beside']
    assert beside['count_2011'] == 214 and beside['used_for_verdict'] is False
    assert beside['bounds'] == [192.6, 235.4]
    assert len(saved['parameters_sha256']) == 64


def test_protocol_never_overwrites_an_old_report(tmp_path):
    out = tmp_path / 'run'
    run_protocol(out, 1, arms=((750, None),), calibration_trials=1, heldout_trials=1, step=0.4)
    with pytest.raises(ValueError, match='already exists'):
        run_protocol(out, 1, arms=((750, None),), calibration_trials=1, heldout_trials=1, step=0.4)


def test_command_line_runs_and_refuses_an_existing_directory(tmp_path, capsys):
    out = tmp_path / 'cli'
    args = ['--run-seed', '5', '--arms', '750', '--calibration-trials', '1', '--heldout-trials', '2',
            '--mortality-step', '0.4', '--output', str(out)]
    assert main(args) == 0
    assert 'verdict' in capsys.readouterr().out
    assert main(args) == 1
    assert 'already exists' in capsys.readouterr().out


def test_the_run_seed_is_required():
    with pytest.raises(SystemExit):
        main(['--output', 'unused'])


def test_spread_matches_statistics_median():
    values = [3, 1, 4, 1, 5, 9, 2, 6]
    assert history.spread(values)['median'] == statistics.median(values)
