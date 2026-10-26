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
    assert meta['model_calls_attempted'] == 7
    assert meta['model_calls_completed'] == dict(researcher=3, developer=2, evaluator=2)
    assert meta['historical_validation'] == 'not_assessed'
    assert len(meta['code_sha256']) == 10
    records = [json.loads(x) for x in (result.run_dir / 'model-calls.jsonl').read_text().splitlines()]
    assert len(records) == 14 and all(r['prompt_version'] for r in records)


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
