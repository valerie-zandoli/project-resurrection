"""An error inside a tool is a defect that propagates; only arguments that do not fit are refused."""

import pytest

from harness.provider import FakeProvider
from harness.roles import run_role


def call(name, **arguments):
    return dict(text="", tool_calls=[dict(name=name, arguments=arguments)])


def say(text):
    return dict(text=text, tool_calls=[])


def test_a_type_error_inside_a_tool_is_a_defect_that_propagates():
    def broken():
        return 1 + "a"

    provider = FakeProvider([call("check_artifacts"), say("done")])
    with pytest.raises(TypeError):
        run_role("evaluator", provider, "check", {"check_artifacts": broken})


def test_arguments_that_do_not_fit_are_still_refused_and_the_tool_never_runs():
    ran = []
    provider = FakeProvider([call("check_artifacts", stray=1), say("done")])
    outcome = run_role("evaluator", provider, "check", {"check_artifacts": lambda: ran.append(1)})
    assert ran == [] and "bad arguments" in provider.calls[1]["messages"][-1]["content"]
    assert "check_artifacts" not in outcome["tool_results"]
