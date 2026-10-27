"""Interactive previews preserve model results and restrict local run requests."""
import io
import json
import threading
from types import SimpleNamespace

import pytest

from report import experiment_controls as controls

SETTINGS = dict(food=4.6, area=100, months=3, population=20, seed=42)


@pytest.mark.parametrize('key,value', [
    ('food', -1), ('food', float('nan')), ('food', float('inf')),
    ('area', 0), ('area', 1001), ('months', 121), ('months', 1.5),
    ('population', 6), ('population', 204), ('seed', True),
    ('seed', '42'), ('seed', -1), ('seed', 10**400),
])
def test_invalid_settings_do_not_create_output(tmp_path, key, value):
    with pytest.raises(ValueError):
        controls.run_experiment({**SETTINGS, key: value}, tmp_path)
    assert not list(tmp_path.iterdir())


def test_saved_results_match_model_and_runs_do_not_overwrite(tmp_path):
    first = controls.run_experiment(SETTINGS, tmp_path)
    folder = tmp_path / first['run_id']
    before = (folder / 'results.json').read_bytes()
    result = json.loads(before)
    config = json.loads((folder / 'input.json').read_text())
    assert result == controls.simulate(config, root=folder / 'snapshot')
    second = controls.run_experiment(SETTINGS, tmp_path)
    assert first['run_id'] != second['run_id']
    assert json.loads((tmp_path / second['run_id'] / 'results.json').read_text())['history'] == result['history']
    assert (folder / 'results.json').read_bytes() == before
    assert (folder / 'viewer.html').is_file()
    record = json.loads((folder / 'preview.json').read_text())
    assert record['settings'] == SETTINGS
    assert record['historical_validation'] == 'not_assessed'
    assert record['research_sha256']


def test_failed_capacity_keeps_existing_files(tmp_path):
    (tmp_path / 'keep.txt').write_text('keep')
    with pytest.raises(ValueError, match='not enough territory'):
        controls.run_experiment({**SETTINGS, 'area': 1, 'population': 200}, tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ['keep.txt']


@pytest.fixture
def server(tmp_path):
    return SimpleNamespace(output_root=tmp_path, source_root=controls.REPO,
                           server_port=8767, origin='http://127.0.0.1:8767',
                           token='test-token', completed=set(), busy=threading.Lock())


def request(server, method, path, body=None, headers=None):
    body = (body or '').encode('utf-8')
    supplied = {'Host': '127.0.0.1:8767', 'Content-Length': str(len(body)),
                'Content-Type': 'application/json', 'Origin': server.origin,
                'X-Experiment-Token': server.token}
    supplied.update(headers or {})
    raw = (f'{method} {path} HTTP/1.0\r\n' + ''.join(f'{k}: {v}\r\n' for k, v in supplied.items()) + '\r\n').encode('latin-1') + body
    output = io.BytesIO()
    socket = SimpleNamespace(settimeout=lambda value: None,
                             makefile=lambda *args: io.BytesIO(raw),
                             sendall=output.write)
    controls.PreviewHandler(socket, ('127.0.0.1', 12345), server)
    header, content = output.getvalue().split(b'\r\n\r\n', 1)
    return int(header.split()[1]), content


def test_local_run_and_only_completed_artifacts_are_served(server):
    assert request(server, 'GET', '/')[0] == 200
    status, body = request(server, 'POST', '/api/runs', json.dumps(SETTINGS))
    assert status == 201, body
    result = json.loads(body)
    for key in ['viewer_url', 'results_url', 'input_url', 'record_url']:
        assert request(server, 'GET', result[key])[0] == 200
    for path in ['/.env', '/runs/../../.env', '/runs/' + result['run_id'] + '/snapshot']:
        assert request(server, 'GET', path)[0] == 404


@pytest.mark.parametrize('headers', [
    {'Origin': 'https://example.com'}, {'Origin': ''},
    {'X-Experiment-Token': ''}, {'X-Experiment-Token': 'é'},
    {'Host': 'example.com'},
])
def test_untrusted_requests_cannot_run(server, headers):
    assert request(server, 'POST', '/api/runs', json.dumps(SETTINGS), headers)[0] == 403
    assert not server.completed


def test_bad_request_and_busy_run(server):
    assert request(server, 'POST', '/api/runs', 'x' * 2049)[0] == 413
    assert request(server, 'POST', '/api/runs', '{')[0] == 400
    assert request(server, 'POST', '/api/runs', '{}', {'Content-Type': 'text/plain'})[0] == 415
    with server.busy:
        assert request(server, 'POST', '/api/runs', json.dumps(SETTINGS))[0] == 409
