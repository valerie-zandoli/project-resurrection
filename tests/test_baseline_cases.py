"""Case files for planted flaws 7 and 8:  what they change, that the validator passes them, that nothing is overwritten."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

from validators.parameters import COLUMNS, EVIDENCE_COLUMNS, validate_parameters

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("baseline_cases", ROOT / "scripts" / "baseline_cases.py")
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)

PARAMETERS = [
    ["age_min", "3", "2", "4", "years", "females", "study_a;summary", "Published"],
    ["density", "4.6", "4.0", "6.0", "rabbits per hectare", "adults", "study_b", "Published"],
]
SOURCES = [
    ["study_a", "Primary A", "study_a"],
    ["study_b", "Primary B", "study_b"],
    ["summary", "Web summary", "unknown"],
    ["report", "Report that cites study B", "study_b;census"],
]
EVIDENCE = [
    ["age_min", "medium", "One study read in full.", "source:study_a~source:summary", "study_a", "Matches the conflict in the notes."],
    ["density", "low", "One study read in part.", "none_identified", "study_b", ""],
]


def write(path, fields, rows):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)
    return path


@pytest.fixture
def inputs(tmp_path):
    return dict(
        parameters=write(tmp_path / "p.csv", COLUMNS, PARAMETERS),
        sources=write(tmp_path / "s.csv", ["key", "citation", "origin"], SOURCES),
        evidence=write(tmp_path / "e.csv", EVIDENCE_COLUMNS, EVIDENCE),
    )


def build(inputs, tmp_path, **changes):
    args = dict(row7="age_min", row8="density", extra_source="report", new_origin="report_as_own")
    args.update(changes)
    return cases.build(inputs["parameters"], inputs["sources"], inputs["evidence"], tmp_path / "out", **args)


def folder_errors(folder):
    return validate_parameters(folder / "parameters.csv", folder / "sources.csv", evidence=folder / "evidence.csv")


def table(folder, name):
    return cases.read_table(folder / name)[1]


def test_the_valid_case_and_both_flawed_cases_pass_the_structural_validator(inputs, tmp_path):
    out = build(inputs, tmp_path)
    for folder in ("valid", "flaw7", "flaw8"):
        assert folder_errors(out / folder) == [], folder


def test_flaw7_changes_only_the_contradiction_and_clears_the_pointer(inputs, tmp_path):
    out = build(inputs, tmp_path)
    valid, flawed = table(out / "valid", "evidence.csv"), table(out / "flaw7", "evidence.csv")
    assert flawed[0]["contradicts"] == "none_identified" and flawed[0]["draft_note"] == ""
    assert {k: v for k, v in flawed[0].items() if k not in ("contradicts", "draft_note")} == \
        {k: v for k, v in valid[0].items() if k not in ("contradicts", "draft_note")}
    assert flawed[1] == valid[1]
    assert (out / "flaw7" / "parameters.csv").read_bytes() == inputs["parameters"].read_bytes()
    assert (out / "flaw7" / "sources.csv").read_bytes() == inputs["sources"].read_bytes()
    key = json.loads((out / "key.json").read_text())["flaw7"]
    assert key["parameter"] == "age_min" and key["dropped_contradictions"] == ["source:study_a~source:summary"]


def test_flaw8_counts_a_repeating_source_as_a_new_origin(inputs, tmp_path):
    out = build(inputs, tmp_path)
    parameters, sources, evidence = (table(out / "flaw8", n) for n in ("parameters.csv", "sources.csv", "evidence.csv"))
    assert parameters[1]["source"] == "study_b;report"
    assert {row["key"]: row["origin"] for row in sources}["report"] == "report_as_own"
    assert evidence[1]["origin"] == "study_b;report_as_own" and evidence[1]["confidence"] == "high"
    assert table(out / "flaw8", "parameters.csv")[0] == table(out / "valid", "parameters.csv")[0]
    key = json.loads((out / "key.json").read_text())["flaw8"]
    assert key["really_repeats"] == ["study_b"] and key["before"]["source_origin"] == "study_b;census"


def test_the_valid_case_is_a_byte_copy_of_the_inputs(inputs, tmp_path):
    out = build(inputs, tmp_path)
    for name, file in (("parameters.csv", "parameters"), ("sources.csv", "sources"), ("evidence.csv", "evidence")):
        assert (out / "valid" / name).read_bytes() == inputs[file].read_bytes()


def test_flaw7_needs_a_named_contradiction(inputs, tmp_path):
    with pytest.raises(ValueError, match="names no contradiction"):
        build(inputs, tmp_path, row7="density")


@pytest.mark.parametrize("changes, message", [
    (dict(extra_source="summary"), "repeats none of the origins"),
    (dict(extra_source="study_b"), "already cited"),
    (dict(new_origin="study_a"), "already in use"),
    (dict(row8="missing"), "not found"),
])
def test_flaw8_refuses_a_plant_that_would_not_be_a_real_repeat(inputs, tmp_path, changes, message):
    with pytest.raises(ValueError, match=message):
        build(inputs, tmp_path, **changes)


def test_nothing_is_written_when_a_case_cannot_be_built_and_nothing_is_overwritten(inputs, tmp_path):
    with pytest.raises(ValueError):
        build(inputs, tmp_path, row7="density")
    assert not (tmp_path / "out").exists()
    build(inputs, tmp_path)
    with pytest.raises(ValueError, match="already exists"):
        build(inputs, tmp_path)


def test_the_command_reports_errors_in_one_line_and_returns_nonzero(inputs, tmp_path, capsys):
    args = ["--parameters", str(inputs["parameters"]), "--sources", str(inputs["sources"]),
            "--evidence", str(inputs["evidence"]), "--output", str(tmp_path / "out"),
            "--row7", "age_min", "--row8", "density", "--extra-source", "report", "--new-origin", "report_as_own"]
    assert cases.main(args) == 0 and "key.json" in capsys.readouterr().out
    assert cases.main(args) == 1 and "already exists" in capsys.readouterr().out
