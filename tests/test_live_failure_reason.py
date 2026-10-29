"""A failed live call says why (found by the shake-down of 2026-10-29, when "(ProviderError)" hid a cut-off reply).  No key."""

import json

import pytest

from harness.live_case import CallBudget, RecordedProvider
from harness.provider import ProviderError
from harness.trace import Trace


class Failing:
    def __init__(self, error):
        self.error = error

    def complete(self, system, messages, tools):
        raise self.error


def recorded(tmp_path, error):
    trace = Trace(tmp_path / "model-calls.jsonl")
    return RecordedProvider("researcher", Failing(error), CallBudget(12), trace), tmp_path / "model-calls.jsonl"


def test_a_provider_error_keeps_its_own_reason(tmp_path):
    provider, log = recorded(tmp_path, ProviderError("Claude reply was cut off at the 4000-token limit"))
    with pytest.raises(ProviderError, match=r"live researcher request failed \(Claude reply was cut off at the 4000-token limit\)"):
        provider.complete("rules", [], [])
    assert "cut off at the 4000-token limit" in json.loads(log.read_text().splitlines()[-1])["message"]


def test_another_exception_still_shows_only_its_class_never_its_text(tmp_path):
    provider, log = recorded(tmp_path, RuntimeError("request headers: sk-ant-secret-key-1234567890"))
    with pytest.raises(ProviderError, match=r"request failed \(RuntimeError\)") as error:
        provider.complete("rules", [], [])
    assert "sk-ant" not in str(error.value) and "sk-ant" not in log.read_text()
