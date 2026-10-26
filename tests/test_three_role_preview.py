"""Integration expectations for the scripted three-role path; no key or network."""

import json
import shutil

import pytest

from harness.provider import FakeProvider
from harness.run_case import HarnessError
from harness import three_role_preview as pipeline
from simulation.model import REPO

OPTIONS = dict(seed=7, months=12, food=4.6, area=50)


def say(text):
    return dict(text=text, tool_calls=[])


def call(name, **arguments):
    return dict(text="", tool_calls=[dict(name=name, arguments=arguments)])


def test_one_case_reaches_all_three_roles_and_keeps_real_artifacts(tmp_path):
    providers = pipeline.scripted_providers()
    output = tmp_path / "case"
    result = pipeline.run_three_role_case(output, providers=providers, options=OPTIONS)
    assert result.status == "pass" and result.attempts == 1
    manifest = json.loads((output / "pipeline.json").read_text())
    assert manifest["mode"] == "scripted_preview"
    results = json.loads((output / "round_0/results.json").read_text())
    evaluation = json.loads((output / "round_0/evaluation.json").read_text())
    assert results["data_kind"] == "simulation" and len(results["history"]) == 13
    assert evaluation["status"] == "pass"
    assert evaluation["historical_validation"] == "not_assessed"
    records = [json.loads(line) for line in (output / "roles.jsonl").read_text().splitlines()]
    assert [r["role"] for r in records] == ["researcher"] * 3 + ["developer"] * 2 + ["evaluator"] * 2
    assert all(r["input_hashes"] and r["prompt_version"] for r in records)
    for role in providers:
        assert (output / f"round_0/{role}.json").exists()
        assert len(providers[role].calls[0]["messages"]) == 1
    assert "Researcher explanation" not in providers["evaluator"].calls[0]["messages"][0]["content"]
    with pytest.raises(HarnessError, match="already exists"):
        pipeline.run_three_role_case(output, providers=providers, options=OPTIONS)


@pytest.mark.parametrize("role,reason", [
    ("researcher", "must read both"), ("developer", "did not call run_model"),
    ("evaluator", "did not call check_artifacts"),
])
def test_skipping_a_required_tool_fails_without_accepting_model_text(tmp_path, role, reason):
    providers = pipeline.scripted_providers()
    providers[role] = FakeProvider([say("Everything passes.")])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and reason in result.reason
    assert not (tmp_path / "case/round_1").exists()
    if role == "researcher":
        assert providers["developer"].calls == []


def test_invalid_research_stops_before_any_role_or_simulation(tmp_path):
    root = tmp_path / "source"
    for relative in pipeline.RESEARCH_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    (root / pipeline.RESEARCH_FILES[0]).write_text("invalid table\n")
    providers = pipeline.scripted_providers()
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers,
                                          options=OPTIONS, source_root=root)
    assert result.status == "rejected" and result.attempts == 0
    assert all(p.calls == [] for p in providers.values())


def test_duplicate_execution_is_not_silently_run_again(tmp_path):
    providers = pipeline.scripted_providers()
    providers["developer"] = FakeProvider([call("run_model"), call("run_model")])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and "only once" in result.reason
    assert providers["evaluator"].calls == []


def test_misleading_explanations_cannot_override_the_verdict_or_revision_cap(tmp_path, monkeypatch):
    original = pipeline.simulator_developer

    def wrong(config, round_number, issues, root):
        results = original(config, round_number, issues, root)
        results["persisted"] = not results["persisted"]
        return results

    monkeypatch.setattr(pipeline, "simulator_developer", wrong)
    providers = pipeline.scripted_providers()
    providers["evaluator"] = FakeProvider([
        reply for _ in range(4) for reply in (call("check_artifacts"), say("It passes!"))
    ])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "stop" and result.attempts == 4 and result.issues
    assert not (tmp_path / "case/round_4").exists()
    assert len(providers["researcher"].calls) == 3
    task = providers["developer"].calls[2]["messages"][0]["content"]
    assert "Prior code-check issues" in task and "requested_change" in task


def test_unknown_research_key_fails_without_reading_arbitrary_files(tmp_path):
    providers = pipeline.scripted_providers()
    providers["researcher"] = FakeProvider([call("read_research", key="../../.env")])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and "unknown research key" in result.reason
    assert providers["developer"].calls == []


def test_role_step_limit_is_preserved(tmp_path):
    providers = pipeline.scripted_providers()
    providers["researcher"] = FakeProvider([call("read_research", key="parameters")] * 5)
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and "no final answer in 4 steps" in result.reason
