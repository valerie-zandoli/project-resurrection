"""Traces preserve observable decisions while redacting every persisted field."""

import json

import pytest

from harness.provider import FakeProvider
from harness.roles import load_prompt, run_role
from harness.trace import Trace, sanitize


def entries(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_context_and_tool_turns_reconstruct_the_visible_conversation(tmp_path):
    path = tmp_path / "roles.jsonl"
    task = "Inspect these inputs. " * 80
    assistant = "I will inspect the evidence first. " * 40
    provider = FakeProvider([
        dict(text=assistant, tool_calls=[dict(id="call-1", name="read_research", arguments=dict(key="evidence"))]),
        dict(text="done", tool_calls=[]),
    ])
    trace = Trace(path)
    trace.run_id = "preview-7"
    trace.revision_round = 2
    run_role("researcher", provider, task, {"read_research": lambda key: "x" * 1000}, trace=trace)
    lines = entries(path)
    assert lines[0]["context"]["system"] == load_prompt("researcher")[1]
    assert lines[0]["context"]["task"] == task == provider.calls[0]["messages"][0]["content"]
    assert lines[1]["context"]["text"] == assistant
    assert lines[2]["context"]["tool_result"] == provider.calls[1]["messages"][-1]["content"]
    assert lines[2]["tool_call_id"] == "call-1"
    assert len({line["role_call_id"] for line in lines}) == 1
    assert all(line["case_id"] == tmp_path.name and line["run_id"] == "preview-7"
               and line["revision_round"] == 2 for line in lines)
    assert len(lines[2]["tool_result_summary"]) == 400
    assert len(lines[2]["context"]["tool_result"]) > 1000


def test_model_visible_truncation_notes_are_distinct_from_trace_summary_cuts(tmp_path, monkeypatch):
    import harness.roles as roles
    monkeypatch.setattr(roles, "MAX_TOOL_RESULT", 500)
    path = tmp_path / "roles.jsonl"
    run_role("evaluator", FakeProvider([
        dict(text="", tool_calls=[dict(name="check_artifacts", arguments={})]),
        dict(text="done", tool_calls=[]),
    ]), "check", {"check_artifacts": lambda: "x" * 800}, trace=Trace(path))
    line = next(line for line in entries(path) if line["event"] == "tool_result")
    assert line["model_removed_text"] == ["cut 300 characters"]
    assert any("cut 100 characters" in note for note in line["removed_text"])
    assert len(line["context"]["tool_result"]) == 500


@pytest.mark.parametrize("credential", ["sk-" + "sentinel" * 4, "ghp_" + "sentinel" * 4,
                                       "github_pat_" + "sentinel" * 4, "Bearer sentinel12345",
                                       "api_key=sentinel12345", "password=sentinel12345"])
def test_metadata_and_context_are_scrubbed_before_persistence(tmp_path, credential):
    path = tmp_path / "trace.jsonl"
    trace = Trace(path)
    trace.run_id = credential
    trace.input_hashes = {credential: credential}
    trace.add(credential, credential, tool=credential, tool_args={"api_key": "unrecognized-format"},
              prompt_version=credential, evaluator_status=credential,
              role_call_id=credential, tool_call_id=credential, context={"task": credential})
    saved = path.read_text()
    assert credential not in saved and "unrecognized-format" not in saved
    assert entries(path)[0]["removed_text"]


def test_structured_secrets_are_scrubbed_without_losing_other_context():
    value, notes = sanitize({"text": "inspect", "nested": [{"Authorization": "custom secret"}]})
    assert value["text"] == "inspect" and "custom secret" not in json.dumps(value)
    assert notes


def test_structured_tool_secrets_are_redacted_before_repr_or_model_delivery(tmp_path):
    path = tmp_path / "roles.jsonl"
    provider = FakeProvider([
        dict(text="", tool_calls=[dict(name="check_artifacts", arguments={})]),
        dict(text="done", tool_calls=[]),
    ])
    run_role("evaluator", provider, "check", {"check_artifacts": lambda: {
        "access_token": "unrecognized-format", "status": "ok"}}, trace=Trace(path))
    assert "unrecognized-format" not in path.read_text()
    assert "unrecognized-format" not in provider.calls[1]["messages"][-1]["content"]
    assert "ok" in provider.calls[1]["messages"][-1]["content"]


def test_two_trace_objects_cannot_claim_the_same_new_file(tmp_path):
    path = tmp_path / "trace.jsonl"
    first, second = Trace(path), Trace(path)
    first.add("harness", "first")
    with pytest.raises(FileExistsError):
        second.add("harness", "second")
    assert len(entries(path)) == 1 and entries(path)[0]["message"] == "first"


def test_provider_failure_is_recorded_without_changing_failure_behavior(tmp_path):
    class BrokenProvider:
        def complete(self, *args):
            raise RuntimeError("api_key=sentinel12345")

    path = tmp_path / "roles.jsonl"
    with pytest.raises(RuntimeError):
        run_role("evaluator", BrokenProvider(), "check", {}, trace=Trace(path))
    assert entries(path)[-1]["event"] == "role_error"
    assert "sentinel12345" not in path.read_text()
