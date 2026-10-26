"""The evidence gate:  a final run is refused on unchecked evidence, and the labels reach case.json."""

import csv
import json
import shutil
from pathlib import Path

import pytest

from harness import __main__ as cli
from harness.evidence_gate import EVIDENCE_FILE, STAGES, check_evidence
from harness.run_case import CaseResult, HarnessError, run_case
from harness.snapshot import RESEARCH_FILES
from simulation.model import REPO
from validators.handoff_hashes import file_sha256

OPTIONS = dict(seed=3, months=24, food=4.6, area=50)
FINAL = dict(OPTIONS, stage="final")


def make_source(tmp_path, change=None, evidence=True):
    """Copies of the research files and the evidence file; `change(rows)` edits the evidence rows."""
    source = tmp_path / "source"
    for relative in (*RESEARCH_FILES, *([EVIDENCE_FILE] if evidence else [])):
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, source / relative)
    if change:
        path = source / EVIDENCE_FILE
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        change(rows)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fields)
            writer.writeheader()
            writer.writerows(rows)
    return source


def clean(rows):
    """Every row medium confidence with no conflict, so a test can set exactly the rows it needs."""
    for row in rows:
        row["confidence"], row["contradicts"] = "medium", "none_identified"


def one_not_checked(rows):
    clean(rows)
    rows[0]["contradicts"] = "not_checked"


def case_json(folder):
    return json.loads((folder / "case.json").read_text())


def test_a_final_run_is_refused_when_a_contradiction_check_is_not_done(tmp_path):
    source = make_source(tmp_path, one_not_checked)
    name = next(csv.DictReader((source / EVIDENCE_FILE).open()))["name"]
    ran = []
    result = run_case(tmp_path / "case", options=FINAL, source_root=source,
                      developer=lambda *args: ran.append(1))
    assert result.status == "rejected" and "evidence gate" in result.reason and name in result.reason
    assert ran == [] and not (tmp_path / "case" / "snapshot").exists()
    case = case_json(tmp_path / "case")
    assert case["notify"] == ["Valerie", "Anastasiya"] and case["evidence"]["not_checked"] == [name]


def test_the_same_table_runs_as_a_pilot_with_a_warning(tmp_path):
    source = make_source(tmp_path, one_not_checked)
    name = next(csv.DictReader((source / EVIDENCE_FILE).open()))["name"]
    result = run_case(tmp_path / "case", options=OPTIONS, source_root=source)
    assert result.status == "pass"
    assert len(result.evidence["warnings"]) == 1 and name in result.evidence["warnings"][0]
    assert case_json(tmp_path / "case")["evidence"]["not_checked"] == [name]
    gate_line = [json.loads(line) for line in (tmp_path / "case/trace.jsonl").read_text().splitlines()][1]
    assert "evidence gate passed (pilot)" in gate_line["message"] and name in gate_line["validator_verdict"]


@pytest.mark.parametrize("stage", STAGES)
def test_a_malformed_label_rejects_the_case_before_anything_runs(tmp_path, stage):
    def bad_label(rows):
        rows[0]["confidence"] = "certain"
    source = make_source(tmp_path, bad_label)
    ran = []
    result = run_case(tmp_path / "case", options=dict(OPTIONS, stage=stage), source_root=source,
                      developer=lambda *args: ran.append(1))
    assert result.status == "rejected" and "evidence file failed validation" in result.reason
    assert ran == [] and not (tmp_path / "case" / "snapshot").exists()


def test_low_rows_and_recorded_conflicts_are_listed_and_never_block(tmp_path):
    def some_labels(rows):
        clean(rows)
        rows[0]["confidence"] = "low"
        rows[1]["contradicts"] = f"parameter:{rows[2]['name']}"
    source = make_source(tmp_path, some_labels)
    with (source / EVIDENCE_FILE).open() as handle:
        names = [row["name"] for row in csv.DictReader(handle)]
    result = run_case(tmp_path / "case", options=FINAL, source_root=source)
    assert result.status == "pass"
    evidence = case_json(tmp_path / "case")["evidence"]
    assert evidence["low"] == [names[0]] and evidence["not_checked"] == [] and evidence["warnings"] == []
    assert evidence["conflicts"] == {names[1]: [f"parameter:{names[2]}"]}
    assert evidence["confidence"] == {"low": 1, "medium": len(names) - 1}


def test_case_json_names_the_evidence_file_by_hash(tmp_path):
    source = make_source(tmp_path)
    run_case(tmp_path / "case", options=OPTIONS, source_root=source)
    evidence = case_json(tmp_path / "case")["evidence"]
    assert evidence["file"] == EVIDENCE_FILE and evidence["stage"] == "pilot"
    assert evidence["sha256"] == file_sha256(source / EVIDENCE_FILE)


def test_a_missing_evidence_file_warns_in_a_pilot_and_refuses_a_final_run(tmp_path):
    source = make_source(tmp_path, evidence=False)
    pilot = run_case(tmp_path / "pilot", options=OPTIONS, source_root=source)
    assert pilot.status == "pass" and "no evidence file" in pilot.evidence["warnings"][0]
    final = run_case(tmp_path / "final", options=FINAL, source_root=source)
    assert final.status == "rejected" and "final run refused: no evidence file" in final.reason
    assert not (tmp_path / "final" / "snapshot").exists()


def test_an_unknown_stage_is_refused_before_a_folder_is_made(tmp_path):
    with pytest.raises(HarnessError, match="stage must be one of"):
        run_case(tmp_path / "case", options=dict(OPTIONS, stage="finl"))
    assert not (tmp_path / "case").exists()
    with pytest.raises(ValueError):
        check_evidence(REPO, *(REPO / relative for relative in RESEARCH_FILES), "finl")


def test_the_command_line_takes_a_stage_and_prints_the_warnings(tmp_path, capsys, monkeypatch):
    seen = {}

    def fake_run_case(output, *, options):
        seen.update(options)
        return CaseResult("pass", "every check passed", 1, [], Path(output),
                          dict(warnings=["the contradiction check is not done for x (a final run is refused)"]))
    monkeypatch.setattr(cli, "run_case", fake_run_case)
    assert cli.main(["--preview", "--stage", "final", "--output", str(tmp_path / "case")]) == 0
    assert seen["stage"] == "final"
    assert "Evidence warning:  the contradiction check is not done for x" in capsys.readouterr().out
    assert cli.main(["--preview", "--output", str(tmp_path / "case2")]) == 0 and seen["stage"] == "pilot"
    with pytest.raises(SystemExit):
        cli.main(["--preview", "--stage", "later", "--output", str(tmp_path / "case3")])
