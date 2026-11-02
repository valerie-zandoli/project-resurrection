import json

import pytest

from harness.live_case import run_live_case
from harness.provider import FakeProvider
from harness.run_case import HarnessError
from harness.three_role_preview import scripted_providers

OPTIONS = dict(seed=7, months=12, food=4.6, area=50)


def test_injected_case_runs_real_tools_but_never_claims_live_claude(tmp_path):
    providers = scripted_providers()
    result = run_live_case(tmp_path / 'case', options=OPTIONS,
                           provider_factory=providers.__getitem__)
    assert result.status == 'pass'
    meta = json.loads((result.run_dir / 'live.json').read_text())
    assert meta['mode'] == 'injected_provider_test'
    # The Researcher reads the two tables and the evidence file in one step (#104), so it makes two calls.
    assert meta['model_calls_attempted'] == 6
    assert meta['model_calls_completed'] == dict(researcher=2, developer=2, evaluator=2)
    assert meta['historical_validation'] == 'not_assessed'
    assert len(meta['code_sha256']) == 10
    records = [json.loads(x) for x in (result.run_dir / 'model-calls.jsonl').read_text().splitlines()]
    assert len(records) == 12 and all(r['prompt_version'] for r in records)


def test_shared_budget_stops_before_an_extra_provider_request(tmp_path):
    providers = scripted_providers()
    result = run_live_case(tmp_path / 'case', options=OPTIONS,
                           provider_factory=providers.__getitem__, max_calls=2)
    assert result.status == 'failed'
    assert len(providers['researcher'].calls) == 2
    assert providers['developer'].calls == providers['evaluator'].calls == []
    assert json.loads((result.run_dir / 'live.json').read_text())['model_calls_attempted'] == 2


def test_provider_failure_is_recorded_without_private_error_text(tmp_path):
    class Broken:
        def complete(self, *args):
            raise RuntimeError('private-request-header sk-ant-secret-value-abcdefghijklmnop')
    result = run_live_case(tmp_path / 'case', options=OPTIONS, provider_factory=lambda role: Broken())
    assert result.status == 'failed'
    for path in result.run_dir.rglob('*'):
        if path.is_file() and path.suffix in ('.json', '.jsonl', '.md'):
            assert 'private-request-header' not in path.read_text()
            assert 'sk-ant-secret-value' not in path.read_text()
    meta = json.loads((result.run_dir / 'live.json').read_text())
    assert meta['model_calls_completed'] == dict.fromkeys(('researcher', 'developer', 'evaluator'), 0)


def test_model_claim_cannot_replace_the_evaluators_required_tool(tmp_path):
    providers = scripted_providers()
    providers['evaluator'] = FakeProvider([dict(text='Everything passes!', tool_calls=[])])
    result = run_live_case(tmp_path / 'case', options=OPTIONS, provider_factory=providers.__getitem__)
    assert result.status == 'failed' and 'did not call check_artifacts' in result.reason


def test_existing_folder_is_refused_before_creating_providers(tmp_path):
    with pytest.raises(HarnessError, match='already exists'):
        run_live_case(tmp_path, options=OPTIONS,
                       provider_factory=lambda role: pytest.fail('must not start'))


def test_run_model_declaration_accepts_no_model_controlled_arguments():
    from harness.litellm_provider import _tool_spec
    assert _tool_spec('run_model')['function']['parameters'] == {
        'type': 'object', 'properties': {}, 'additionalProperties': False}


@pytest.mark.parametrize('role', ('researcher', 'developer', 'evaluator'))
@pytest.mark.parametrize('blank', ('', ' \n\t'))
@pytest.mark.parametrize('after_tools', (False, True))
def test_empty_final_answers_fail_without_advancing_the_handoff(tmp_path, role, blank, after_tools):
    providers = scripted_providers()
    if after_tools:
        providers[role].replies[1] = dict(text=blank, tool_calls=[])
    else:
        providers[role] = FakeProvider([dict(text=blank, tool_calls=[])])
    result = run_live_case(tmp_path / 'case', options=OPTIONS,
                           provider_factory=providers.__getitem__)
    assert result.status == 'failed'
    assert f'{role} returned an empty final answer' in result.reason
    roles = ('researcher', 'developer', 'evaluator')
    for later in roles[roles.index(role) + 1:]:
        assert providers[later].calls == []
    records = [json.loads(line) for line in (result.run_dir / 'roles.jsonl').read_text().splitlines()]
    assert any(record['role'] == role and 'empty final answer' in record['message']
               and record['prompt_version'] for record in records)
    assert not (result.run_dir / 'round_0' / 'evaluation.json').exists()
