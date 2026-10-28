"""Integration expectations for the scripted three-role path; no key or network."""

import json
import shutil
from pathlib import Path

import pytest

from harness.provider import FakeProvider
from harness.run_case import HarnessError
from harness.snapshot import EVIDENCE_FILE, SNAPSHOT_FILES
from harness import three_role_preview as pipeline
from simulation.model import REPO
from validators.handoff_hashes import file_sha256

OPTIONS = dict(seed=7, months=12, food=4.6, area=50)


def say(text):
    return dict(text=text, tool_calls=[])


def call(name, **arguments):
    return dict(text="", tool_calls=[dict(name=name, arguments=arguments)])


def calls(*names):
    """One reply that asks for several calls at once; it differs from a single call, so it is not a stuck loop."""
    return dict(text="", tool_calls=[dict(name=name, arguments={}) for name in names])


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
    # the Researcher reads the three files in one step (three tool calls), then answers
    assert [r["role"] for r in records] == ["researcher"] * 4 + ["developer"] * 2 + ["evaluator"] * 2
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
    providers["developer"] = FakeProvider([call("run_model"), calls("run_model", "run_model")])
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
    assert len(providers["researcher"].calls) == 2  # one step of reads, one answer, once per case
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
    providers["researcher"] = FakeProvider([call("read_research", key=key) for key in
                                            ("parameters", "sources", "evidence", "parameters", "sources")])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and "no final answer in 4 steps" in result.reason


def test_a_second_check_artifacts_call_fails_and_is_not_run_again(tmp_path):
    providers = pipeline.scripted_providers()
    providers["evaluator"] = FakeProvider([call("check_artifacts"), calls("check_artifacts", "check_artifacts")])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and "only once" in result.reason


def test_the_manifest_says_scripted_only_for_the_scripted_stand_ins(tmp_path):
    scripted = pipeline.run_three_role_case(tmp_path / "scripted", providers=pipeline.scripted_providers(),
                                            options=OPTIONS)
    assert json.loads((scripted.run_dir / "pipeline.json").read_text())["mode"] == "scripted_preview"

    class Supplied:  # not a FakeProvider, so the run must not be called scripted
        def __init__(self, inner):
            self.inner = inner

        def complete(self, *args):
            return self.inner.complete(*args)

    wrapped = {role: Supplied(provider) for role, provider in pipeline.scripted_providers().items()}
    supplied = pipeline.run_three_role_case(tmp_path / "supplied", providers=wrapped, options=OPTIONS)
    assert json.loads((supplied.run_dir / "pipeline.json").read_text())["mode"] == "provider_supplied_unverified"


def test_a_changed_snapshot_stops_the_case_before_the_simulator_runs(tmp_path, monkeypatch):
    ran = []
    monkeypatch.setattr(pipeline, "check_files_current", lambda config, root: ["research file changed"])
    monkeypatch.setattr(pipeline, "simulator_developer", lambda *args: ran.append(1))
    result = pipeline.run_three_role_case(tmp_path / "case", providers=pipeline.scripted_providers(),
                                          options=OPTIONS)
    assert result.status == "failed" and "snapshot changed" in result.reason
    assert ran == []


def test_the_researcher_reads_the_evidence_file_and_the_run_records_which_version(tmp_path):
    providers = pipeline.scripted_providers()
    output = tmp_path / "case"
    assert pipeline.run_three_role_case(output, providers=providers, options=OPTIONS).status == "pass"
    saved = json.loads((output / "round_0/researcher.json").read_text())
    assert saved["evidence_file"] == pipeline.EVIDENCE_FILE
    assert saved["evidence_sha256"] == file_sha256(REPO / pipeline.EVIDENCE_FILE)
    first_label = (REPO / pipeline.EVIDENCE_FILE).read_text().splitlines()[1].split(",")[1]  # a confidence label
    evidence_result = providers["researcher"].calls[1]["messages"][-1]["content"]
    assert "UNTRUSTED SOURCE TEXT" in evidence_result and first_label in evidence_result  # data, not instructions


def test_the_researcher_reads_the_evidence_bytes_that_the_gate_checked(tmp_path, monkeypatch):
    source = tmp_path / "source"
    for relative in SNAPSHOT_FILES:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    original_run_case = pipeline.run_case

    def change_source_before_research(output, *, options, source_root, developer, evaluator,
                                      max_rounds=3):
        def change_then_run(config, round_number, issues, root):
            (Path(source_root) / EVIDENCE_FILE).write_text("changed after snapshot\\n", encoding="utf-8")
            return developer(config, round_number, issues, root)

        return original_run_case(output, options=options, source_root=source_root,
                                 developer=change_then_run, evaluator=evaluator,
                                 max_rounds=max_rounds)

    monkeypatch.setattr(pipeline, "run_case", change_source_before_research)
    providers = pipeline.scripted_providers()
    output = tmp_path / "case"
    result = pipeline.run_three_role_case(output, providers=providers, options=OPTIONS, source_root=source)
    snapshot_evidence = output / "snapshot" / EVIDENCE_FILE
    saved = json.loads((output / "round_0/researcher.json").read_text())
    assert result.status == "pass"
    assert saved["evidence_sha256"] == file_sha256(snapshot_evidence)
    assert saved["evidence_sha256"] == json.loads((output / "case.json").read_text())["evidence"]["sha256"]
    assert saved["evidence_sha256"] != file_sha256(source / EVIDENCE_FILE)
    evidence_result = providers["researcher"].calls[1]["messages"][-1]["content"]
    original_first_label = (snapshot_evidence.read_text().splitlines()[1].split(",")[1])
    assert original_first_label in evidence_result


def test_a_researcher_that_skips_the_evidence_file_fails(tmp_path):
    providers = pipeline.scripted_providers()
    providers["researcher"] = FakeProvider([call("read_research", key="parameters"),
                                            call("read_research", key="sources"), say("Done.")])
    result = pipeline.run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "failed" and "evidence file" in result.reason
    assert providers["developer"].calls == []


def test_a_missing_evidence_file_is_reported_to_the_researcher_not_hidden(tmp_path):
    root = tmp_path / "source"
    for relative in pipeline.RESEARCH_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    providers = pipeline.scripted_providers()
    output = tmp_path / "case"
    result = pipeline.run_three_role_case(output, providers=providers, options=OPTIONS, source_root=root)
    assert result.status == "pass"
    assert "NO EVIDENCE FILE" in providers["researcher"].calls[1]["messages"][-1]["content"]
    assert json.loads((output / "round_0/researcher.json").read_text())["evidence_sha256"] is None


def test_the_command_prints_the_caption_first_and_last_and_the_manifest_carries_it(tmp_path, capsys):
    output = tmp_path / "case"
    assert pipeline.main(["--preview", "--seed", "7", "--months", "12", "--output", str(output)]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    caption = "Caption: scripted preview; the Researcher inspects existing tables"
    assert lines[0] == caption and lines[-1] == caption
    assert json.loads((output / "pipeline.json").read_text())["caption"] == pipeline.CAPTION
