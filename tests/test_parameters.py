import csv

import pytest

from validators.parameters import COLUMNS, EVIDENCE_COLUMNS, validate_parameters


def files(tmp_path, **changes):
    row = dict(zip(COLUMNS, ["survival", "0.8", "0.6", "1", "annual probability",
                            "adults", "paper;summary", "Published estimate"]))
    row.update(changes)
    parameters = tmp_path / "parameters.csv"
    with parameters.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    sources = tmp_path / "sources.csv"
    sources.write_text(
        "key,citation,origin\n"
        "paper,Primary study,study_a\n"
        "summary,Summary,study_b\n"
    )
    return parameters, sources


def evidence_file(tmp_path, **changes):
    row = dict(zip(EVIDENCE_COLUMNS, ["survival", "medium", "One study supports this estimate.",
                                     "none_identified", "study_a", ""]))
    row.update(changes)
    evidence = tmp_path / "evidence.csv"
    with evidence.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVIDENCE_COLUMNS)
        writer.writeheader()
        writer.writerow(row)
    return evidence


def test_accepts_decimals_multiple_sources_and_quoted_text(tmp_path):
    assert validate_parameters(*files(tmp_path, evidence_or_assumption="Assumed, test range")) == []


@pytest.mark.parametrize("changes,expected", [
    ({"baseline": "NaN"}, "finite number"),
    ({"high": "inf"}, "finite number"),
    ({"low": "oops"}, "finite number"),
    ({"baseline": "2"}, "low <= baseline <= high"),
    ({"low": "2", "high": "1"}, "low <= baseline <= high"),
    ({"source": "missing"}, "source key"),
    ({"source": "paper;"}, "source key"),
    ({"units": " "}, "units is required"),
    ({"evidence_or_assumption": ""}, "evidence_or_assumption is required"),
])
def test_rejects_bad_values(tmp_path, changes, expected):
    assert any(expected in error for error in validate_parameters(*files(tmp_path, **changes)))


def test_rejects_duplicate_parameters(tmp_path):
    parameters, sources = files(tmp_path)
    with parameters.open("a") as handle:
        handle.write(parameters.read_text().splitlines()[1] + "\n")
    assert any("duplicate parameter" in e for e in validate_parameters(parameters, sources))


def test_rejects_missing_columns_and_missing_file(tmp_path):
    parameters, sources = files(tmp_path)
    parameters.write_text("name,baseline\nx,1\n")
    assert any("expected columns" in e for e in validate_parameters(parameters, sources))
    sources.unlink()
    assert any("cannot read" in e for e in validate_parameters(parameters, sources))


def test_rejects_duplicate_sources(tmp_path):
    parameters, sources = files(tmp_path)
    sources.write_text("key\npaper\npaper\nsummary\n")
    assert any("unique" in e for e in validate_parameters(parameters, sources))


def test_rejects_ragged_csv(tmp_path):
    parameters, sources = files(tmp_path)
    with parameters.open("a") as handle:
        handle.write("too,few,fields\n")
    assert any("number of CSV fields" in e for e in validate_parameters(parameters, sources))


def test_empty_tables_fail(tmp_path):
    parameters, sources = files(tmp_path)
    parameters.write_text(",".join(COLUMNS) + "\n")
    sources.write_text("key\n")
    assert len(validate_parameters(parameters, sources)) == 2


def test_accepts_evidence_columns_with_known_parameter_sources(tmp_path):
    parameters, sources = files(tmp_path)
    evidence = evidence_file(tmp_path)
    assert validate_parameters(parameters, sources, evidence=evidence) == []


@pytest.mark.parametrize("changes,expected", [
    ({"confidence": "certain"}, "confidence must be low, medium, or high"),
    ({"confidence_reason": " "}, "confidence_reason is required"),
    ({"origin": "study_c"}, "not listed by a cited source"),
    ({"contradicts": "source:missing~source:paper"}, "unknown source in contradiction"),
    ({"contradicts": "parameter:missing"}, "unknown or invalid parameter contradiction"),
    ({"contradicts": "not_checked;source:paper~source:summary"}, "must stand alone"),
])
def test_rejects_invalid_evidence_columns(tmp_path, changes, expected):
    parameters, sources = files(tmp_path)
    evidence = evidence_file(tmp_path, **changes)
    assert any(expected in error for error in
               validate_parameters(parameters, sources, evidence=evidence))


def test_accepts_unknown_origin_and_not_checked_as_disclosed_values(tmp_path):
    parameters, sources = files(tmp_path)
    evidence = evidence_file(tmp_path, contradicts="not_checked", origin="unknown")
    sources.write_text("key,citation,origin\npaper,Primary study,unknown\nsummary,Summary,unknown\n")
    assert validate_parameters(parameters, sources, evidence=evidence) == []


def test_evidence_rows_must_match_parameter_names_exactly(tmp_path):
    parameters, sources = files(tmp_path)
    evidence = evidence_file(tmp_path, name="not_a_parameter")
    errors = validate_parameters(parameters, sources, evidence=evidence)
    assert any("parameter name is not in the parameter table" in error for error in errors)
    assert any("missing evidence row for parameter 'survival'" in error for error in errors)
