import json

import pytest

from report.final_history import read_final_history
from test_experiment_controls import request, server


def test_saved_final_result_and_read_only_route(server, monkeypatch):
    from simulation import history
    def forbidden(*args, **kwargs):
        pytest.fail('Displaying results must never run the historical test')
    monkeypatch.setattr(history, 'run_protocol', forbidden)
    status, body = request(server, 'GET', '/api/history-final')
    report = json.loads(body)
    assert status == 200
    assert report == read_final_history()
    assert report['run_seed'] == 20261101
    assert report['verdict']['result'] == 'pass'
    assert not list(server.output_root.iterdir())


def test_mismatched_verdict_is_rejected(tmp_path):
    report = read_final_history()
    report['areas'][0]['heldout']['count_2011']['median'] = 1000
    path = tmp_path / 'report.json'
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='verdict'):
        read_final_history(path)
