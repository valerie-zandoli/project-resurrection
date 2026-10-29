"""Saved-run evaluation uses a fresh role and cannot accept model prose as a verdict."""
import json

import pytest

from harness.provider import FakeProvider
from harness.roles import RoleError
from report.experiment_controls import run_experiment
from report.preview_evaluator import evaluate_preview
from tests.test_experiment_controls import SETTINGS, request, server


def scripted_evaluator(text='The artifact checks passed. Historical accuracy is not assessed.'):
    return FakeProvider([
        dict(tool_calls=[dict(name='check_artifacts', arguments={})]),
        dict(text=text, tool_calls=[]),
    ])


@pytest.fixture
def run(tmp_path):
    result = run_experiment(SETTINGS, tmp_path)
    return tmp_path / result['run_id']


def test_fresh_role_checks_saved_bytes_and_saves_report(run):
    before = (run / 'results.json').read_bytes()
    provider = scripted_evaluator('Everything checked. sk-abcdefghijklmnopqrstuv')
    report = evaluate_preview(run, provider_factory=lambda: provider)
    assert report['evaluation']['status'] == 'pass'
    assert report['evaluation']['run_id'] == run.name
    assert report['evaluation']['historical_validation'] == 'not_assessed'
    assert report['evaluation']['checks']
    assert report['input_sha256']['results.json']
    assert 'sk-abcdefghijklmnopqrstuv' not in json.dumps(report)
    assert (run / 'results.json').read_bytes() == before
    assert len(provider.calls) == 2
    assert provider.calls[0]['tools'] == ['check_artifacts']
    folder = run / 'reviews' / report['review_id']
    assert (folder / 'report.json').is_file()
    assert 'sk-abcdefghijklmnopqrstuv' not in (folder / 'trace.jsonl').read_text()


def test_prose_pass_cannot_override_failed_check(run):
    result = json.loads((run / 'results.json').read_text())
    result['history'][1]['population'] += 1
    (run / 'results.json').write_text(json.dumps(result))
    report = evaluate_preview(run, provider_factory=lambda: scripted_evaluator('Everything passes!'))
    assert report['evaluation']['status'] == 'revise'
    assert report['evaluation']['issues']


def test_missing_tool_call_produces_no_accepted_report(run):
    with pytest.raises(RoleError):
        evaluate_preview(run, provider_factory=lambda: FakeProvider([dict(text='Pass', tool_calls=[])]))
    assert not list((run / 'reviews').glob('*/report.json'))


def test_changed_research_stops_before_provider(run):
    research = run / 'snapshot/data/parameters/iberian_lynx_baseline.csv'
    research.chmod(0o644)
    research.write_text(research.read_text() + '\n')
    def forbidden():
        pytest.fail('A changed snapshot must not reach Claude')
    with pytest.raises(ValueError, match='snapshot changed'):
        evaluate_preview(run, provider_factory=forbidden)


def test_failed_provider_never_persists_exception_details(run):
    def broken():
        raise RuntimeError('private credential content')
    with pytest.raises(RuntimeError):
        evaluate_preview(run, provider_factory=broken)
    trace = next((run / 'reviews').glob('*/trace.jsonl')).read_text()
    assert 'private credential' not in trace
    assert not list((run / 'reviews').glob('*/report.json'))


def test_endpoint_caches_review_and_refuses_arbitrary_runs(server):
    status, content = request(server, 'POST', '/api/runs', json.dumps(SETTINGS))
    run_id = json.loads(content)['run_id']
    providers = []
    def fresh():
        provider = scripted_evaluator()
        providers.append(provider)
        return provider
    server.provider_factory = fresh
    path = f'/api/runs/{run_id}/evaluate'
    status, body = request(server, 'POST', path, '{}')
    assert status == 201, body
    report = json.loads(body)
    assert request(server, 'POST', path, '{}')[0] == 200
    assert len(providers) == 1
    assert request(server, 'GET', report['report_url'])[0] == 200
    assert request(server, 'POST', path, '{}', {'Origin': 'https://example.com'})[0] == 403
    assert request(server, 'POST', '/api/runs/interactive-' + 'a'*32 + '/evaluate', '{}')[0] == 404
    assert request(server, 'POST', path, '{"seed":1}')[0] == 400


def test_failed_evaluation_is_not_pass_and_retries_are_bounded(server):
    _, content = request(server, 'POST', '/api/runs', json.dumps(SETTINGS))
    run_id = json.loads(content)['run_id']
    path = f'/api/runs/{run_id}/evaluate'
    for _ in range(3):
        status, body = request(server, 'POST', path, '{}')
        assert status == 502
        assert 'no verdict was accepted' in json.loads(body)['error']
    assert request(server, 'POST', path, '{}')[0] == 429
    assert run_id not in server.reviews
    assert request(server, 'GET', f'/runs/{run_id}/results.json')[0] == 200
