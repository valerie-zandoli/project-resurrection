"""Research comparisons report saved input values, not inferred wildlife observations."""
import csv
import json
import shutil

import pytest

from report.experiment_controls import run_experiment
from report.research_comparison import research_comparison
from simulation.model import load_parameters
from simulation.model import REPO
from tests.test_experiment_controls import SETTINGS


def test_valid_source_spacing_does_not_break_experiment(tmp_path):
    source = tmp_path / 'research'
    shutil.copytree(REPO / 'data/parameters', source / 'data/parameters')
    path = source / 'data/parameters/iberian_lynx_baseline.csv'
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        columns, rows = reader.fieldnames, list(reader)
    for row in rows:
        row['source'] = ' ; '.join(row['source'].split(';'))
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    result = run_experiment(SETTINGS, tmp_path / 'runs', source_root=source)
    breeding = next(row for row in result['comparison']['rows'] if row['name'] == 'breeding_age_min')
    assert [item['key'] for item in breeding['sources']] == ['palomares2005', 'catsg']
    assert all(item['citation'] for row in result['comparison']['rows'] for item in row['sources'])


@pytest.mark.parametrize('food,allows', [(1, False), (4.6, True), (55, True)])
def test_comparison_matches_saved_research_and_run(tmp_path, food, allows):
    run = run_experiment({**SETTINGS, 'food': food}, tmp_path)
    folder = tmp_path / run['run_id']
    config = json.loads((folder / 'input.json').read_text())
    results = json.loads((folder / 'results.json').read_text())
    data = run['comparison']
    assert data == json.loads((folder / 'research-comparison.json').read_text())
    assert data['run_id'] == run['run_id']
    assert data['food'] == food and data['food_allows_breeding'] is allows
    parameters = load_parameters(config, folder / 'snapshot')
    rows = {row['name']: row for row in data['rows']}
    assert rows['female_home_range_km2']['used_value'] == parameters.home_range
    assert rows['annual_breeding_probability']['used_value'] == parameters.breeding_probability
    assert rows['litter_size_at_birth']['used_value'] == [parameters.litter_min, parameters.litter_max]
    assert rows['cub_cumulative_survival_10mo']['used_value'] == parameters.survival_10
    with (folder / 'snapshot' / config['parameters_csv']).open(newline='') as handle:
        research = {row['name']: row for row in csv.DictReader(handle)}
    for name, row in rows.items():
        assert row['research_value'] == float(research[name]['baseline'])
        assert row['sources'] and row['evidence_note']
    assert data['outcomes']['final_population'] == results['history'][-1]['population']
    assert data['historical_validation'] == 'not_assessed'
    if not allows:
        assert data['outcomes']['births'] == 0


def test_applied_override_is_distinct_from_research_estimate(tmp_path):
    run = run_experiment(SETTINGS, tmp_path)
    folder = tmp_path / run['run_id']
    config = json.loads((folder / 'input.json').read_text())
    results = json.loads((folder / 'results.json').read_text())
    config['parameter_overrides']['female_home_range_km2'] = 10
    data = research_comparison(config, results, folder / 'snapshot')
    row = next(row for row in data['rows'] if row['name'] == 'female_home_range_km2')
    assert row['used_value'] == 10
    assert row['research_value'] == run['comparison']['rows'][1]['research_value']
    assert data['patches'][0]['female_capacity'] == 10
