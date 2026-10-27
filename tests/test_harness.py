"""The offline harness skeleton:  every guarantee is code, and none needs a model or a key."""

import ast
import json
import os
import shutil
import stat
from pathlib import Path

import pytest

from harness import __main__ as cli
import harness.run_case as run_case_module
from harness.run_case import HarnessError, run_case, simulator_developer
from harness.snapshot import EVIDENCE_FILE, RESEARCH_FILES, SNAPSHOT_FILES, make_snapshot
from harness.trace import Trace, scrub
from simulation.model import REPO
from validators.handoff_hashes import file_sha256
from validators.results_checks import build_evaluation

OPTIONS = dict(seed=3, months=24, food=4.6, area=50)


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def flip_persisted(results):
    results["persisted"] = not results["persisted"]
    return results


def flaky_developer(bad_rounds):
    """A Developer whose results are wrong in the given rounds and right afterwards."""
    def developer(config, round_number, issues, root):
        results = simulator_developer(config, round_number, issues, root)
        return flip_persisted(results) if round_number in bad_rounds else results
    developer.seen_issues = []
    return developer


def test_a_clean_case_passes_in_round_0_and_writes_every_file(tmp_path):
    result = run_case(tmp_path / "case", options=OPTIONS)
    assert (result.status, result.attempts, result.issues) == ("pass", 1, [])
    out = tmp_path / "case"
    for name in ("input.json", "results.json", "evaluation.json"):
        assert (out / "round_0" / name).exists()
    case = json.loads((out / "case.json").read_text())
    assert case["status"] == "pass" and case["notify"] == [] and case["run_ids"] == ["preview-3"]
    assert case["clarification"] is None
    assert case["research_sha256"].keys() == set(SNAPSHOT_FILES)
    assert not (out / "round_1").exists()


def test_the_snapshot_is_read_only_and_matches_the_source(tmp_path):
    hashes = make_snapshot(REPO, tmp_path / "snap")
    for relative in SNAPSHOT_FILES:
        copy = tmp_path / "snap" / relative
        assert stat.S_IMODE(copy.stat().st_mode) == 0o444
        assert hashes[relative] == file_sha256(REPO / relative) == file_sha256(copy)
    with pytest.raises(FileExistsError):
        make_snapshot(REPO, tmp_path / "snap")


def test_the_evidence_gate_uses_the_same_snapshot_the_researcher_reads(tmp_path, monkeypatch):
    source = tmp_path / "source"
    for relative in SNAPSHOT_FILES:
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, target)
    original = run_case_module.make_snapshot

    def snapshot_then_change_source(source_root, snapshot_root):
        hashes = original(source_root, snapshot_root)
        evidence = Path(source_root) / EVIDENCE_FILE
        evidence.write_text("not,the,validated,evidence\\n", encoding="utf-8")
        return hashes

    monkeypatch.setattr(run_case_module, "make_snapshot", snapshot_then_change_source)
    result = run_case(tmp_path / "case", options=OPTIONS, source_root=source)
    case = json.loads((result.run_dir / "case.json").read_text())
    snapshot_evidence = result.run_dir / "snapshot" / EVIDENCE_FILE
    assert result.status == "pass"
    assert case["evidence"]["sha256"] == file_sha256(snapshot_evidence)
    assert case["research_sha256"][EVIDENCE_FILE] == file_sha256(snapshot_evidence)
    assert case["evidence"]["sha256"] != file_sha256(source / EVIDENCE_FILE)


def test_the_run_is_built_from_the_snapshot_not_the_source(tmp_path):
    run_case(tmp_path / "case", options=OPTIONS)
    config = json.loads((tmp_path / "case/round_0/input.json").read_text())
    snapshot = tmp_path / "case" / "snapshot"
    assert config["parameters_sha256"] == file_sha256(snapshot / config["parameters_csv"])
    assert config["sources_sha256"] == file_sha256(snapshot / config["sources_csv"])


def test_a_wrong_result_goes_back_with_its_issues_and_a_fixed_one_passes(tmp_path):
    seen = []

    def developer(config, round_number, issues, root):
        seen.append((round_number, [i["code"] for i in issues]))
        return flaky_developer({0, 1})(config, round_number, issues, root)

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer)
    assert (result.status, result.attempts) == ("pass", 3)
    assert seen == [(0, []), (1, ["persistence_recomputed"]), (2, ["persistence_recomputed"])]
    assert json.loads((tmp_path / "case/round_1/evaluation.json").read_text())["status"] == "revise"


def test_the_case_stops_after_round_3_and_never_runs_a_fifth_attempt(tmp_path):
    result = run_case(tmp_path / "case", options=OPTIONS, developer=flaky_developer({0, 1, 2, 3, 4}))
    assert (result.status, result.attempts) == ("stop", 4)
    assert not (tmp_path / "case" / "round_4").exists()
    case = json.loads((tmp_path / "case/case.json").read_text())
    assert case["notify"] == ["Valerie", "Anastasiya"]
    assert case["clarification"] is None
    assert case["issues"] and case["issues"][0]["code"] == "persistence_recomputed"
    assert "round 3" in case["reason"]


def test_the_harness_caps_the_rounds_even_if_the_evaluator_never_says_stop(tmp_path):
    def evaluator(config, results, root, round_number):
        # A schema-valid evaluation that never says stop:  the harness accepts nothing else as a record.
        evaluation = build_evaluation(config, results, root, round_number)
        evaluation.update(status="revise", issues=[dict(code="x", message="m", requested_change="c")])
        return evaluation

    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=evaluator)
    assert (result.status, result.attempts) == ("stop", 4)


def test_a_changed_research_file_rejects_the_case_without_retry(tmp_path):
    def developer(config, round_number, issues, root):
        results = simulator_developer(config, round_number, issues, root)
        target = root / config["parameters_csv"]  # tamper after the run, as a Researcher edit would
        os.chmod(target, 0o644)
        target.write_text(target.read_text().replace("breeding_age_min,3,", "breeding_age_min,4,"))
        return flip_persisted(results)

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer)
    assert result.status == "rejected" and "changed since" in result.reason
    assert result.attempts == 1 and not (tmp_path / "case" / "round_1").exists()


def test_a_changed_evidence_snapshot_rejects_the_case(tmp_path):
    def developer(config, round_number, issues, root):
        evidence = root / EVIDENCE_FILE
        os.chmod(evidence, 0o644)
        evidence.write_text("changed after validation\\n", encoding="utf-8")
        return simulator_developer(config, round_number, issues, root)

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer)
    assert result.status == "rejected" and "snapshot changed" in result.reason
    assert EVIDENCE_FILE in result.reason
    assert result.attempts == 1


def test_a_developer_that_raises_is_reported_and_never_retried(tmp_path):
    calls = []

    def developer(config, round_number, issues, root):
        calls.append(round_number)
        raise RuntimeError("model crashed")

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer)
    assert (result.status, calls) == ("failed", [0])
    assert "RuntimeError" in result.reason and "no retry" in result.reason


def test_an_evaluator_that_raises_is_reported_and_never_retried(tmp_path):
    calls = []

    def evaluator(config, results, root, round_number):
        calls.append(round_number)
        raise ValueError("checker crashed")

    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=evaluator)
    assert (result.status, calls) == ("failed", [0])


def test_results_with_other_hashes_are_rejected(tmp_path):
    def developer(config, round_number, issues, root):
        results = simulator_developer(config, round_number, issues, root)
        results["config"]["parameters_sha256"] = "1" * 64
        return results

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer)
    assert result.status == "rejected" and "hash mismatch" in result.reason


def test_a_bad_research_table_stops_the_case_before_anything_runs(tmp_path):
    source = tmp_path / "source"
    for relative in RESEARCH_FILES:
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, source / relative)
    table = source / RESEARCH_FILES[0]
    table.write_text(table.read_text().replace("name,baseline,", "name,base,", 1))
    ran = []
    result = run_case(tmp_path / "case", options=OPTIONS, source_root=source,
                      developer=lambda *args: ran.append(1))
    assert result.status == "rejected" and "failed validation" in result.reason
    assert ran == [] and not (tmp_path / "case" / "snapshot").exists()
    assert json.loads((tmp_path / "case/case.json").read_text())["notify"] == ["Valerie", "Anastasiya"]


def test_an_existing_output_folder_is_never_overwritten(tmp_path):
    (tmp_path / "case").mkdir()
    with pytest.raises(HarnessError, match="already exists"):
        run_case(tmp_path / "case", options=OPTIONS)


def test_the_trace_is_one_numbered_json_line_per_step_in_a_fixed_shape(tmp_path):
    run_case(tmp_path / "case", options=OPTIONS, developer=flaky_developer({0}))
    steps = lines(tmp_path / "case" / "trace.jsonl")
    assert [s["step"] for s in steps] == list(range(1, len(steps) + 1))
    keys = {"step", "role", "prompt_version", "input_hashes", "message", "tool", "tool_args",
            "tool_result_summary", "validator_verdict", "evaluator_status", "revision_round", "removed_text",
            "sent_chars", "received_chars"}
    assert all(set(s) == keys for s in steps)
    roles = [s["role"] for s in steps]
    assert {"harness", "developer", "evaluator"} <= set(roles)
    assert roles[0] == "harness" and steps[-1]["message"].startswith("case finished")
    assert [s["evaluator_status"] for s in steps if s["role"] == "evaluator"] == ["revise", "pass"]
    assert steps[2]["input_hashes"].keys() == set(SNAPSHOT_FILES)


def test_a_trace_never_holds_a_key_and_shows_what_it_cut():
    text, notes = scrub("token sk-ant-abcdefghijklmnopqrstuvwx and more")
    assert "sk-ant" not in text and "redacted" in notes[0]
    text, notes = scrub("x" * 1000)
    assert len(text) == 400 and notes == ["cut 600 characters"]


def test_the_trace_file_is_scrubbed_and_never_overwritten(tmp_path):
    trace = Trace(tmp_path / "t.jsonl")
    trace.add("developer", "key is sk-ant-abcdefghijklmnopqrstuvwx")
    assert "sk-ant" not in (tmp_path / "t.jsonl").read_text()
    assert "redacted" in lines(tmp_path / "t.jsonl")[0]["removed_text"][0]
    with pytest.raises(FileExistsError):
        Trace(tmp_path / "t.jsonl")


def test_the_harness_calls_no_model_and_opens_no_network():
    banned = {"anthropic", "litellm", "openai", "requests", "urllib", "socket", "http", "subprocess"}
    for path in (REPO / "harness").glob("*.py"):
        if path.name == "litellm_provider.py":
            continue  # Live model access is isolated in this opt-in adapter; the offline harness stays clean.
        tree = ast.parse(path.read_text())
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        assert not imported & banned, f"{path.name} imports {imported & banned}"
    adapter = ast.parse((REPO / "harness" / "litellm_provider.py").read_text())
    adapter_imports = {a.name.split(".")[0] for n in ast.walk(adapter) if isinstance(n, ast.Import) for a in n.names}
    adapter_imports |= {n.module.split(".")[0] for n in ast.walk(adapter)
                        if isinstance(n, ast.ImportFrom) and n.module}
    assert adapter_imports & banned == {"litellm"}


def test_command_line_exit_codes(tmp_path, capsys):
    base = ["--preview", "--seed", "3", "--months", "24"]
    assert cli.main(base + ["--output", str(tmp_path / "ok")]) == 0
    assert "pass" in capsys.readouterr().out
    assert cli.main(base + ["--output", str(tmp_path / "ok")]) == 2
    assert "failed to start" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(["--output", str(tmp_path / "x")])
