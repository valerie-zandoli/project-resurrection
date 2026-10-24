"""Six gaps found in the line-by-line review of the simulator preview (PR 40).

Each test pins a behavior that the code already has but no test held.  Synthetic fixtures only.
"""

import json
import math
import os
import random
import subprocess
import sys
from dataclasses import replace

import jsonschema
import pytest

from simulation.__main__ import main
from simulation.model import Lynx, REPO, advance, load_parameters, preview_config, simulate


@pytest.fixture
def config():
    return preview_config()


@pytest.fixture
def params(config):
    return load_parameters(config, REPO)


# Gap 1: a female who finds room in both patches stays in her own.
@pytest.mark.parametrize('home', ['A', 'B'])
def test_unsettled_female_settles_in_her_own_patch_when_both_have_room(config, params, home):
    p = replace(params, annual_mortality=0, breeding_probability=0)
    config['male_patch_crossing_probability'] = 0
    animals = [Lynx('f', 'female', 20, home)]
    row = advance(animals, config, p, random.Random(1), 1, {'A': 2, 'B': 2})
    assert animals[0].settled and animals[0].patch_id == home
    assert row['movements'] == 0


# Gap 2: males cross only from the breeding minimum age, counted after that month's aging.
@pytest.mark.parametrize('age,crosses', [(33, False), (34, False), (35, True), (60, True)])
def test_only_males_of_breeding_minimum_age_cross(config, params, age, crosses):
    config['male_patch_crossing_probability'] = 1
    p = replace(params, annual_mortality=0, breeding_probability=0)
    animals = [Lynx('m', 'male', age, 'A')]
    row = advance(animals, config, p, random.Random(0), 1, {'A': 1, 'B': 1})
    assert (animals[0].patch_id == 'B') == crosses
    assert row['movements'] == (1 if crosses else 0)


# Gap 3: the --input path.
def test_cli_input_file_is_used_and_its_hashes_are_checked(tmp_path, config):
    path = tmp_path / 'input.json'
    path.write_text(json.dumps(config))
    out = tmp_path / 'out'
    assert main(['--preview', '--input', str(path), '--seed', '1', '--output', str(out)]) == 0
    written = json.loads((out / 'results.json').read_text())
    assert written['seed'] == config['seed']  # --seed applies only to a generated input
    assert written == simulate(config)
    path.write_text(json.dumps(dict(config, parameters_sha256='0' * 64)))
    refused = tmp_path / 'refused'
    assert main(['--preview', '--input', str(path), '--output', str(refused)]) == 1
    assert not refused.exists()


# Gap 4: overrides outside the agreed ranges, and the effect of the home range on capacity.
@pytest.mark.parametrize('override', [
    dict(annual_mortality_rate_all_causes=0.6),
    dict(annual_mortality_rate_all_causes=0.05),
    dict(female_home_range_km2=40),
    dict(female_home_range_km2=3),
    dict(rabbit_density_spring_min_for_territorial_breeding=7),
    dict(rabbit_density_spring_min_for_territorial_breeding=2.5),
    dict(unknown_parameter=1),
])
def test_out_of_range_or_unknown_overrides_are_rejected(config, override):
    config['parameter_overrides'] = override
    with pytest.raises(jsonschema.ValidationError):
        simulate(config)


def test_home_range_override_changes_territory_capacity(config):
    config['initial_population'].update(females=20, males=20)  # 10 females per patch
    for patch in config['patches']:
        patch['area_km2'] = 50
    with pytest.raises(ValueError, match='territory capacity'):
        simulate(config)  # 50 km2 / 10 km2 = 5 slots per patch
    config['parameter_overrides'] = dict(female_home_range_km2=4)  # 12 slots per patch
    result = simulate(config)
    assert result['config']['parameter_overrides'] == dict(female_home_range_km2=4)


# Gap 5: the invariants, over many seeds and both areas.
@pytest.mark.parametrize('area', [50, 100])
@pytest.mark.parametrize('seed', range(1, 13))
def test_invariants_hold_for_many_seeds(seed, area):
    result = simulate(preview_config(seed=seed, months=24, area=area))
    history, animals = result['history'], result['final_animals']
    for old, new in zip(history, history[1:]):
        assert new['population'] == old['population'] + new['births'] - new['deaths']
        assert new['population'] == new['females'] + new['males']
    assert len({a['id'] for a in animals}) == len(animals)
    for patch in ('A', 'B'):
        held = sum(a['alive'] and a['settled'] and a['patch_id'] == patch for a in animals)
        assert held <= math.floor(area / 10)
    assert all(not a['settled'] for a in animals if a['sex'] == 'male' or not a['alive'])


# Gap 6: a replay in a fresh process, with a different hash seed, gives the same bytes.
def test_replay_is_identical_across_separate_processes(tmp_path):
    outputs = []
    for index, hash_seed in enumerate(('0', '12345')):
        out = tmp_path / f'run{index}'
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        done = subprocess.run([sys.executable, '-m', 'simulation', '--preview', '--months', '24',
                               '--seed', '7', '--output', str(out)],
                              cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, done.stdout + done.stderr
        outputs.append((out / 'results.json').read_bytes())
    assert outputs[0] == outputs[1]
