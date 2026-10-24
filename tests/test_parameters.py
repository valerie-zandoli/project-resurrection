import csv

import pytest

from validators.parameters import COLUMNS, validate_parameters


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
    sources.write_text("key,citation\npaper,Primary study\nsummary,Summary\n")
    return parameters, sources


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
