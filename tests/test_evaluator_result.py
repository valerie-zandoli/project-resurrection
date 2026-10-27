"""What the harness does when the Evaluator hands back something that is not an evaluation.

The code check is the record, so the harness must never use an Evaluator result that did not come
from a successful `check_artifacts` call, and must fail the case (no retry) instead of crashing.
"""

import pytest

from harness.provider import FakeProvider
from harness.roles import model_evaluator, run_role
from harness.run_case import run_case

OPTIONS = dict(seed=3, months=24, food=4.6, area=50)


def call(name, **arguments):
    return dict(text="", tool_calls=[dict(name=name, arguments=arguments)])


def say(text):
    return dict(text=text, tool_calls=[])


@pytest.mark.parametrize("returned", ["refused:  bad arguments for check_artifacts", {"status": "pass"}, None, []],
                         ids=["a_refusal_string", "a_dict_without_the_schema_fields", "nothing", "a_list"])
def test_run_case_fails_the_case_when_the_evaluator_returns_something_that_is_not_an_evaluation(tmp_path, returned):
    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=lambda *args: returned)
    assert result.status == "failed" and "evaluator failed" in result.reason and "no retry" in result.reason
    assert (tmp_path / "case" / "case.json").exists()
    assert not (tmp_path / "case" / "round_0" / "evaluation.json").exists()


def test_a_model_that_calls_the_check_with_a_stray_argument_fails_the_case_without_crashing(tmp_path):
    provider = FakeProvider([call("check_artifacts", stray=1), say("done")])
    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=model_evaluator(provider))
    assert result.status == "failed" and "check_artifacts" in result.reason


def test_a_refused_call_never_replaces_a_real_tool_result():
    provider = FakeProvider([call("check_artifacts"), call("check_artifacts", stray=1), say("done")])
    outcome = run_role("evaluator", provider, "check", {"check_artifacts": lambda: {"status": "pass"}})
    assert outcome["tool_results"] == {"check_artifacts": {"status": "pass"}}


def test_a_good_check_followed_by_a_refused_call_still_passes_a_clean_case(tmp_path):
    provider = FakeProvider([call("check_artifacts"), call("check_artifacts", stray=1), say("Every check passed.")])
    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=model_evaluator(provider))
    assert result.status == "pass"
