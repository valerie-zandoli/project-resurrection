"""The primary-source audit draw:  reproducible, 10 distinct rows, nothing overwritten."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_sample", ROOT / "scripts" / "audit_sample.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture(scope="module")
def parameters():
    return audit.read(ROOT / audit.PARAMETERS)


def names(rows):
    return [row["name"] for row in rows]


def test_the_seed_is_the_first_8_bytes_of_sha256_of_the_run_id():
    expected = int.from_bytes(hashlib.sha256(b"batch-001").digest()[:8], "big")
    # A change to the rule changes this number on purpose:  edit it only with a reason in the commit.
    assert audit.seed_for("batch-001") == expected == 12688271005249962704
    assert audit.seed_for("batch-001") != audit.seed_for("batch-002")


def test_the_draw_is_10_distinct_rows_and_the_same_for_one_run_id(parameters):
    first = audit.draw("batch-001", parameters)
    assert len(first) == 10 and len(set(names(first))) == 10
    assert names(first) == names(audit.draw("batch-001", list(reversed(parameters))))


def test_the_rows_drawn_for_one_run_id_are_pinned(parameters):
    # random.sample may change between Python versions; this pin makes any drift visible.  Edit it only with a reason.
    assert names(audit.draw("batch-001", parameters)) == [
        "female_home_range_km2", "breeding_age_max", "cub_cumulative_survival_3mo",
        "cub_cumulative_survival_to_dispersal", "food_level_medium_rabbits_per_ha", "diet_rabbit_fraction",
        "rabbit_density_autumn_min_for_territorial_breeding", "rabbit_density_spring_min_for_territorial_breeding",
        "dispersal_settlement_fraction", "litter_size_at_birth"]


def test_another_run_id_draws_other_rows(parameters):
    draws = {tuple(names(audit.draw(f"batch-{i:03d}", parameters))) for i in range(20)}
    assert len(draws) > 10


def test_every_row_is_drawn_sometimes_so_no_parameter_escapes_the_audit(parameters):
    seen = {n for i in range(300) for n in names(audit.draw(f"batch-{i}", parameters))}
    assert seen == {row["name"] for row in parameters}


def test_bad_requests_are_refused(parameters):
    with pytest.raises(ValueError):
        audit.draw("", parameters)
    with pytest.raises(ValueError):
        audit.draw("batch", parameters, 0)
    with pytest.raises(ValueError):
        audit.draw("batch", parameters, len(parameters) + 1)


def test_the_sheet_names_the_seed_the_rows_and_how_each_source_was_read(parameters):
    rows = audit.draw("batch-001", parameters)
    sheet = audit.render("batch-001", rows, audit.read(ROOT / audit.SOURCES))
    assert str(audit.seed_for("batch-001")) in sheet
    assert all(f"`{row['name']}`" in sheet for row in rows)
    assert "Bar:  9 of 10 correct" in sheet and "Running table" in sheet
    assert sheet.count("\n| ") >= 10 + 2


def test_a_source_missing_from_the_registry_is_named_on_the_sheet():
    row = dict(name="x", baseline="1", low="0", high="2", units="u", area_age_group="g", source="nowhere;real")
    sheet = audit.render("batch-x", [row], [dict(key="real", how_read="full text")])
    assert "nowhere (not in the registry)" in sheet and "real (full text)" in sheet


def test_a_pipe_or_a_newline_cannot_break_the_table():
    assert audit.cell("a|b\nc ") == "a/b c"


def test_the_command_writes_a_sheet_and_never_overwrites_it(tmp_path, capsys):
    out = tmp_path / "audit.md"
    assert audit.main(["--run-id", "batch-001", "--output", str(out)]) == 0
    assert "batch-001" in out.read_text() and "seed" in capsys.readouterr().out
    assert audit.main(["--run-id", "batch-001", "--output", str(out)]) == 1
    assert "already exists" in capsys.readouterr().out
    assert audit.main(["--run-id", "", "--output", str(tmp_path / "x.md")]) == 1
