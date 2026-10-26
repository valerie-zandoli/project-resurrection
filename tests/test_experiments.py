"""Batch orchestration and statistical verification; no scientific approval."""

import hashlib
import json

import pytest

from simulation import experiments
from simulation.model import REPO, preview_config, simulate


def test_seed_rule_has_a_stable_known_vector_and_distinct_streams():
    payload = b'["lynx-preview-batch-v1",42,"food-4.6_area-50",0]'
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big')
    assert experiments.trial_seed(42, 'food-4.6_area-50', 0) == expected
    seeds = {experiments.trial_seed(42, cell, trial)
             for cell, _, _ in experiments.CELLS for trial in range(100)}
    assert len(seeds) == 600
    assert experiments.trial_seed(43, 'food-4.6_area-50', 0) not in seeds


def test_statistics_match_known_wilson_and_interpolated_quantiles():
    records = [dict(status='completed', persisted=bool(i % 2),
                    final_population=i * 10, extinction_month=month)
               for i, month in enumerate([1, None, 3, None])]
    result = experiments.aggregate(records)
    assert result['persistence_share'] == 0.5
    assert result['persistence_wilson_95'] == pytest.approx([0.150038989, 0.849961011])
    assert result['final_population_median'] == 15
    assert result['final_population_p10'] == pytest.approx(3)
    assert result['final_population_p90'] == pytest.approx(27)
    assert result['extinction_share'] == 0.5
    assert result['extinction_month_median'] == 2
    records[0]['status'] = 'failed'
    with pytest.raises(ValueError, match='Only completed'):
        experiments.aggregate(records)


def test_survivors_have_no_invented_extinction_time():
    result = experiments.aggregate([dict(status='completed', persisted=True,
                                        final_population=20, extinction_month=None)])
    assert result['extinction_share'] == 0
    assert result['extinction_month_median'] is None
    assert result['persistence_wilson_95'][1] == pytest.approx(1)


def test_three_replays_keep_all_six_cells_and_single_trial_artifacts(tmp_path):
    reports = [experiments.run_batch(tmp_path / str(i), trials=1, months=12) for i in range(3)]
    assert reports[0] == reports[1] == reports[2]
    report = reports[0]
    assert report['status'] == 'completed'
    assert report['historical_validation'] == 'not_assessed'
    assert len(report['cells']) == 6
    for cell in report['cells']:
        assert cell['status'] == 'completed' and cell['statistics']['trials'] == 1
        record = cell['trials'][0]
        directory = tmp_path / '0' / record['artifacts']
        config = json.loads((directory / 'input.json').read_text())
        result = json.loads((directory / 'results.json').read_text())
        assert result == simulate(config)
        assert config['seed'] == record['seed']
        assert config['food_rabbits_per_ha'] == cell['food_rabbits_per_ha']
        assert {p['area_km2'] for p in config['patches']} == {cell['area_km2_per_patch']}
    before = (tmp_path / '0' / 'batch.json').read_bytes()
    with pytest.raises(FileExistsError):
        experiments.run_batch(tmp_path / '0', trials=1)
    assert (tmp_path / '0' / 'batch.json').read_bytes() == before


def test_failure_is_preserved_and_stops_without_retry_or_complete_statistics(tmp_path, monkeypatch):
    calls = []

    def fail_second(config):
        calls.append(config['seed'])
        saved = json.loads((tmp_path / 'out' / 'batch.json').read_text())
        assert saved['cells'][0]['trials'][-1]['status'] == 'running'
        if len(calls) == 2:
            raise ValueError('planted model defect')
        return simulate(config)

    monkeypatch.setattr(experiments, 'simulate', fail_second)
    report = experiments.run_batch(tmp_path / 'out', trials=3, months=1)
    assert len(calls) == 2
    assert report['status'] == 'incomplete'
    cell = report['cells'][0]
    assert cell['planned_trials'] == 3 and cell['statistics'] is None
    assert [r['status'] for r in cell['trials']] == ['completed', 'failed']
    assert cell['trials'][1]['error'] == 'planted model defect'
    assert all(c['status'] == 'pending' for c in report['cells'][1:])
    assert json.loads((tmp_path / 'out' / 'batch.json').read_text()) == report


def test_research_edit_mid_batch_stops_instead_of_refreshing_hashes(tmp_path, monkeypatch):
    root = tmp_path / 'research'
    (root / 'data/parameters').mkdir(parents=True)
    for filename in ('sources.csv', 'iberian_lynx_baseline.csv'):
        relative = f'data/parameters/{filename}'
        (root / relative).write_bytes((REPO / relative).read_bytes())
    monkeypatch.setattr(experiments, 'preview_config',
                        lambda seed, months, food, area: preview_config(seed, months, food, area, root))
    calls = []

    def edit_after_first(config):
        calls.append(config['sources_sha256'])
        result = simulate(config, root)
        source = root / 'data/parameters/sources.csv'
        source.write_bytes(source.read_bytes() + b'\n')
        return result

    monkeypatch.setattr(experiments, 'simulate', edit_after_first)
    report = experiments.run_batch(tmp_path / 'out', trials=2, months=1)
    assert report['status'] == 'incomplete'
    assert len(calls) == 2 and calls[0] == calls[1]
    assert report['cells'][0]['trials'][1]['status'] == 'failed'


@pytest.mark.parametrize('arguments', [dict(seed=-1), dict(trials=0), dict(months=0), dict(trials=True)])
def test_bad_batch_controls_do_not_create_output(tmp_path, arguments):
    output = tmp_path / 'bad'
    with pytest.raises(ValueError):
        experiments.run_batch(output, **arguments)
    assert not output.exists()


def test_cli_requires_preview_and_reports_success_or_failure(tmp_path):
    with pytest.raises(SystemExit):
        experiments.main(['--output', str(tmp_path / 'missing')])
    args = ['--preview', '--trials', '1', '--months', '1', '--output', str(tmp_path / 'out')]
    assert experiments.main(args) == 0
    assert experiments.main(args) == 1
