"""Expected sensitivity behavior, backward compatibility, and evaluator agreement."""

import copy
import hashlib
import json
from dataclasses import replace

import jsonschema
import pytest

from simulation.__main__ import main
from simulation.experiments import run_batch
from simulation.model import (Lynx, REPO, advance, food_breeding_probability,
                              load_parameters, preview_config, simulate)
from validators.results_checks import build_evaluation, check_birth_timing

LINEAR = 'linear_food_sensitivity'


@pytest.mark.parametrize('food,chance', [(0, 0), (1, .833 / 4.6), (2.3, .4165),
                                       (4.6, .833), (55, .833)])
def test_probability_rises_linearly_then_caps(food, chance):
    config = preview_config(food=food, breeding_rule=LINEAR)
    assert food_breeding_probability(config, load_parameters(config, REPO)) == pytest.approx(chance)


@pytest.mark.parametrize('food,digest', [
    (1, 'cda8bf9fe87246b24a0c255138dd2cd48870da7c870a514227ea1bd2c46af0cd'),
    (4.6, '92d8e35152640e735f909c8b8325f1e17e446c9039c7978f7b3f1a4fd4fd3ecf'),
    (55, 'f5cfb9b7efdc7af515511bfb3211d6d21b66214d7e237e4d954584310188b9a8'),
])
def test_default_matches_saved_pre_change_24_month_result(food, digest):
    # Expected hashes generated from develop before this change, seed 7.
    result = simulate(preview_config(seed=7, months=24, food=food))
    assert hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest() == digest


class FixedRandom:
    def random(self):
        return .4

    def shuffle(self, values):
        pass

    def randint(self, low, high):
        return low


@pytest.mark.parametrize('food,month,male_patch,settled,births', [
    (2.3, 2, 'A', True, 2), (1, 2, 'A', True, 0), (0, 2, 'A', True, 0),
    (2.3, 1, 'A', True, 0), (2.3, 2, 'B', True, 0),
])
def test_linear_rule_still_requires_season_and_local_pair(food, month, male_patch, settled, births):
    config = preview_config(food=food, breeding_rule=LINEAR)
    config['male_patch_crossing_probability'] = 0
    params = replace(load_parameters(config, REPO), annual_mortality=0, litter_min=2, litter_max=2)
    animals = [Lynx('f', 'female', 36, 'A', settled=settled),
               Lynx('m', 'male', 36, male_patch)]
    row = advance(animals, config, params, FixedRandom(), month, {'A': 5, 'B': 5})
    assert row['births'] == births


def test_a_female_without_a_territory_does_not_breed_under_the_linear_rule():
    """She settles first if her patch has a free slot (and then breeds); with none she stays unsettled."""
    config = preview_config(food=2.3, breeding_rule=LINEAR)
    config['male_patch_crossing_probability'] = 0
    params = replace(load_parameters(config, REPO), annual_mortality=0, litter_min=2, litter_max=2)

    def births(slots):
        animals = [Lynx('f', 'female', 36, 'A', settled=False), Lynx('m', 'male', 36, 'A')]
        return advance(animals, config, params, FixedRandom(), 2, {'A': slots, 'B': slots})['births']
    assert births(5) == 2  # a free slot: she settles, then breeds
    assert births(0) == 0  # no slot: she stays unsettled and does not breed


def test_linear_12_month_run_replays_and_passes_independent_checks():
    config = preview_config(seed=7, months=12, food=2.3, breeding_rule=LINEAR)
    results = [simulate(config) for _ in range(3)]
    assert results[0] == results[1] == results[2]
    assert sum(row['births'] for row in results[0]['history']) > 0
    assert config['schema_version'] == '2.2' and results[0]['schema_version'] == '3.2'
    evaluation = build_evaluation(config, results[0], REPO)
    assert evaluation['status'] == 'pass'
    assert evaluation['historical_validation'] == 'not_assessed'


def test_birth_check_distinguishes_step_and_linear_and_keeps_zero_food_closed():
    params = dict(food_threshold=4.6, birth_month=3)
    config = dict(food_rabbits_per_ha=2.3, start_month=1, breeding_rule=LINEAR)
    results = dict(history=[dict(month=0, births=0), dict(month=2, births=1)])
    assert check_birth_timing(config, results, params)[0]
    assert not check_birth_timing(dict(config, breeding_rule='spring_threshold'), results, params)[0]
    assert not check_birth_timing(dict(config, food_rabbits_per_ha=0), results, params)[0]
    results['history'][1]['month'] = 1
    assert not check_birth_timing(config, results, params)[0]


@pytest.mark.parametrize('version', ['2.0', '2.1'])
def test_old_inputs_cannot_silently_select_new_rule(version):
    config = preview_config(breeding_rule=LINEAR)
    config['schema_version'] = version
    if version == '2.0':
        config.pop('settlement_rule')
    with pytest.raises(jsonschema.ValidationError):
        simulate(config)


def test_missing_or_unknown_rule_and_mixed_threshold_axis_are_rejected():
    config = preview_config(breeding_rule=LINEAR)
    missing = copy.deepcopy(config)
    missing.pop('breeding_rule')
    with pytest.raises(jsonschema.ValidationError):
        simulate(missing)
    unknown = dict(config, breeding_rule='unknown')
    with pytest.raises(jsonschema.ValidationError):
        simulate(unknown)
    config['parameter_overrides']['rabbit_density_spring_min_for_territorial_breeding'] = 3
    with pytest.raises(ValueError, match='separately from threshold overrides'):
        simulate(config)


def test_cli_upgrades_legacy_input_before_applying_both_options(tmp_path):
    config = preview_config()
    config.pop('settlement_rule')
    config['schema_version'] = '2.0'
    source = tmp_path / 'old.json'
    source.write_text(json.dumps(config))
    output = tmp_path / 'run'
    assert main(['--preview', '--input', str(source), '--breeding-rule', LINEAR,
                 '--settlement-rule', 'monthly_own_patch_only', '--output', str(output)]) == 0
    saved = json.loads((output / 'input.json').read_text())
    assert saved['schema_version'] == '2.2' and saved['breeding_rule'] == LINEAR
    assert saved['settlement_rule'] == 'monthly_own_patch_only'


def test_batch_labels_rule_and_matches_trial_seeds_to_baseline(tmp_path):
    baseline = run_batch(tmp_path / 'step', seed=7, trials=1, months=12)
    linear = run_batch(tmp_path / 'linear', seed=7, trials=1, months=12, breeding_rule=LINEAR)
    assert baseline['status'] == linear['status'] == 'completed'
    assert baseline['breeding_rule'] == 'spring_threshold' and linear['breeding_rule'] == LINEAR
    assert baseline['batch_id'] != linear['batch_id']
    for step_cell, linear_cell in zip(baseline['cells'], linear['cells']):
        assert step_cell['trials'][0]['seed'] == linear_cell['trials'][0]['seed']
        folder = tmp_path / 'linear' / linear_cell['trials'][0]['artifacts']
        config = json.loads((folder / 'input.json').read_text())
        result = json.loads((folder / 'results.json').read_text())
        assert result['config'] == config and config['breeding_rule'] == LINEAR
        assert build_evaluation(config, result, REPO)['status'] == 'pass'
