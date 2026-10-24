"""Model verification with synthetic fixtures, never historical calibration."""

import copy
import json
import random
import csv
from dataclasses import replace

import jsonschema
import pytest

from simulation.__main__ import main
from simulation.model import (Lynx, REPO, advance, check_states, load_parameters,
                              persisted, preview_config, run_model, schema, simulate, summary)
from validators.handoff_hashes import file_sha256


@pytest.fixture
def config():
    return preview_config()


@pytest.fixture
def params(config):
    return load_parameters(config, REPO)


def test_replay_12_months_is_identical_three_times(config):
    original = copy.deepcopy(config)
    results = [simulate(config) for _ in range(3)]
    assert results[0] == results[1] == results[2]
    assert config == original
    assert len(results[0]['history']) == 13
    jsonschema.validate(results[0], schema('results'))


def test_120_month_accounting_and_real_provenance(config):
    config['duration_months'] = 120
    result = simulate(config)
    assert result['data_kind'] == 'simulation'
    assert result['config']['parameters_sha256'] != '0' * 64
    assert len(result['history']) == 121
    for old, new in zip(result['history'], result['history'][1:]):
        assert new['population'] == old['population'] + new['births'] - new['deaths']
        assert new['population'] == new['females'] + new['males']
    assert len({a['id'] for a in result['final_animals']}) == len(result['final_animals'])
    assert result['history'][-1]['population'] == sum(a['alive'] for a in result['final_animals'])


def test_initial_ages_are_mixed_seeded_and_starting_territories_valid(config, params):
    result = run_model(config, replace(params, annual_mortality=0, breeding_probability=0))
    initial_ages = [a['age_months'] - config['duration_months'] for a in result['final_animals']]
    assert all(36 <= age <= 96 for age in initial_ages)
    assert len(set(initial_ages)) > 1
    for patch in ('A', 'B'):
        assert sum(a['settled'] for a in result['final_animals'] if a['patch_id'] == patch) == 5


def test_conditional_survival_recovers_published_cumulative_values(params):
    assert params.survival(0) ** 3 == pytest.approx(0.75)
    assert params.survival(0) ** 3 * params.survival(3) ** 7 == pytest.approx(0.69)
    assert params.survival(0) ** 3 * params.survival(3) ** 7 * params.survival(10) ** 8 == pytest.approx(0.57)
    assert params.survival(18) ** 12 == pytest.approx(0.63)


@pytest.mark.parametrize('food,expected', [(0, 0), (4.599, 0), (4.6, 4), (55, 4)])
def test_march_threshold_is_inclusive_and_births_come_last(config, params, food, expected):
    config.update(food_rabbits_per_ha=food, male_patch_crossing_probability=0)
    animals = [Lynx('f', 'female', 36, 'A', settled=True), Lynx('m', 'male', 36, 'A')]
    p = replace(params, annual_mortality=0, breeding_probability=1, litter_min=4, litter_max=4)
    row = advance(animals, config, p, random.Random(3), 2, {'A': 5, 'B': 5})
    assert row['births'] == expected
    assert all(a.age_months == 0 and not a.settled for a in animals[2:])
    assert all(a.age_months == 37 for a in animals[:2])


def test_no_births_outside_march_or_without_eligible_male(config, params):
    p = replace(params, annual_mortality=0, breeding_probability=1)
    config['male_patch_crossing_probability'] = 0
    for month, male_patch in [(1, 'A'), (2, 'B')]:
        animals = [Lynx('f', 'female', 36, 'A', settled=True), Lynx('m', 'male', 36, male_patch)]
        assert advance(animals, config, p, random.Random(4), month, {'A': 5, 'B': 5})['births'] == 0


def test_settlement_fills_vacancy_but_never_exceeds_capacity(config, params):
    p = replace(params, annual_mortality=0, breeding_probability=0)
    animals = [Lynx('f1', 'female', 36, 'A', settled=True),
               Lynx('f2', 'female', 20, 'A'), Lynx('f3', 'female', 20, 'A')]
    row = advance(animals, config, p, random.Random(4), 1, {'A': 1, 'B': 1})
    assert row['movements'] == 1
    assert sum(a.settled for a in animals) == 2
    waiting = next(a for a in animals if not a.settled)
    holder = next(a for a in animals if a.settled and a.patch_id == 'B')
    holder.alive = False
    holder.settled = False
    advance(animals, config, p, random.Random(5), 2, {'A': 1, 'B': 1})
    assert waiting.settled and waiting.patch_id == 'B'
    check_states(animals, {'A': 1, 'B': 1})


def test_male_crossing_uses_no_female_slot(config, params):
    config['male_patch_crossing_probability'] = 1
    animals = [Lynx('f', 'female', 36, 'B', settled=True), Lynx('m', 'male', 36, 'A')]
    row = advance(animals, config, replace(params, annual_mortality=0), random.Random(0), 1, {'A': 0, 'B': 1})
    assert animals[1].patch_id == 'B' and not animals[1].settled
    assert row['movements'] == 1 and row['population'] == 2


def test_persistence_requires_living_settled_breeding_age_pair(params):
    female = Lynx('f', 'female', 36, 'A', settled=True)
    male = Lynx('m', 'male', 108, 'A')
    assert persisted([female, male], params)
    for bad_female in [replace(female, settled=False), replace(female, alive=False),
                       replace(female, age_months=35), replace(female, age_months=109)]:
        assert not persisted([bad_female, male], params)
    for bad_male in [replace(male, patch_id='B'), replace(male, alive=False),
                     replace(male, age_months=35), replace(male, age_months=109)]:
        assert not persisted([female, bad_male], params)


def test_zero_food_can_persist_without_births(config, params):
    config.update(food_rabbits_per_ha=0, male_patch_crossing_probability=0)
    config['initial_population'].update(age_months_min=36, age_months_max=36)
    result = run_model(config, replace(params, annual_mortality=0))
    report = summary(result)
    assert report['persisted'] and report['births_final_12_months'] == 0
    assert report['extinction_month'] is None and report['final_population'] == 20


def test_controlled_extinction_releases_territories_and_retains_dead_states(config, params):
    result = run_model(config, replace(params, annual_mortality=1))
    assert summary(result)['extinction_month'] == 1
    assert not result['persisted']
    assert all(not a['alive'] and not a['settled'] and 36 <= a['age_months'] <= 96
               for a in result['final_animals'])
    assert all(row['population'] == 0 for row in result['history'][1:])


@pytest.mark.parametrize('change', ['stale', 'duplicate_patch', 'reversed_ages', 'capacity', 'quality', 'odd_count', 'nan'])
def test_invalid_inputs_stop_before_simulation(config, change):
    if change == 'stale': config['parameters_sha256'] = '0' * 64
    if change == 'duplicate_patch': config['patches'][1]['id'] = 'A'
    if change == 'reversed_ages': config['initial_population']['age_months_min'] = 100
    if change == 'capacity': config['patches'][0]['area_km2'] = 1
    if change == 'quality': config['patches'][0]['habitat_quality'] = 0.5
    if change == 'odd_count': config['initial_population']['females'] = 9
    if change == 'nan': config['food_rabbits_per_ha'] = float('nan')
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        simulate(config)


def test_parameter_overrides_are_recorded_and_applied(config):
    config['parameter_overrides'] = dict(annual_mortality_rate_all_causes=0.2,
                                       female_home_range_km2=4,
                                       rabbit_density_spring_min_for_territorial_breeding=3)
    p = load_parameters(config, REPO)
    assert p.survival(18) ** 12 == pytest.approx(0.8)
    assert p.home_range == 4 and p.food_threshold == 3
    assert simulate(config)['config']['parameter_overrides'] == config['parameter_overrides']


def test_changed_units_fail_even_with_current_hashes(config, tmp_path):
    config['parameters_csv'] = 'parameters.csv'
    config['sources_csv'] = 'sources.csv'
    (tmp_path / 'sources.csv').write_bytes((REPO / 'data/parameters/sources.csv').read_bytes())
    with (REPO / 'data/parameters/iberian_lynx_baseline.csv').open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    rows[0]['units'] = 'months'
    with (tmp_path / 'parameters.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for field in ('parameters', 'sources'):
        config[field + '_sha256'] = file_sha256(tmp_path / config[field + '_csv'])
    with pytest.raises(ValueError, match='unexpected units'):
        simulate(config, tmp_path)


def test_cli_writes_inspectable_artifacts_and_refuses_overwrite(tmp_path):
    output = tmp_path / 'preview'
    assert main(['--preview', '--output', str(output)]) == 0
    assert {p.name for p in output.iterdir()} == {'input.json', 'results.json', 'summary.json', 'history.csv'}
    result = json.loads((output / 'results.json').read_text())
    jsonschema.validate(result, schema('results'))
    before = (output / 'results.json').read_bytes()
    assert main(['--preview', '--output', str(output)]) == 1
    assert (output / 'results.json').read_bytes() == before
