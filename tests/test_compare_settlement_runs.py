import json

import pytest

from scripts import compare_settlement_runs as comparison
from simulation.experiments import aggregate

DEFAULT_SETTLEMENT_RULE = comparison.DEFAULT_SETTLEMENT_RULE
SETTLEMENT_RULES = comparison.SETTLEMENT_RULES


def make_batches(tmp_path, trial_seeds=(1001,)):
    """Three batches, one per settlement rule; each cell has one trial per seed in `trial_seeds`."""
    paths = {}
    for rule in SETTLEMENT_RULES:
        folder = tmp_path / rule
        records = []
        for index, trial_seed in enumerate(trial_seeds):
            artifacts = f"food-4.6_area-50/trial-{index:06d}"
            trial_dir = folder / artifacts
            trial_dir.mkdir(parents=True)
            run_id = f"preview-{rule}-food-4.6_area-50-{index:06d}"
            run_input = {
                "schema_version": "2.1", "run_id": run_id, "seed": trial_seed,
                "purpose": "synthetic_experiment", "duration_months": 12,
                "food_rabbits_per_ha": 4.6, "settlement_rule": rule,
                "patches": [
                    {"id": "A", "area_km2": 50, "habitat_quality": 1.0},
                    {"id": "B", "area_km2": 50, "habitat_quality": 1.0},
                ],
            }
            trial_summary = {
                "run_id": run_id, "persisted": True, "final_population": 20,
                "extinction_month": None, "births_final_12_months": 0,
                "historical_validation": "not_assessed",
                "model_conventions": "proposed-2026-10-22",
            }
            write_json(trial_dir / "input.json", run_input)
            write_json(trial_dir / "results.json", {
                "run_id": run_id, "seed": trial_seed, "config": run_input,
            })
            write_json(trial_dir / "summary.json", trial_summary)
            records.append({
                "trial": index, "seed": trial_seed, "run_id": run_id,
                "artifacts": artifacts, "status": "completed", **trial_summary,
            })
        statistics = aggregate(records)
        batch = {
            "format_version": "preview-batch-1", "purpose": "synthetic_preview",
            "historical_validation": "not_assessed", "settlement_rule": rule,
            "seed": 13, "seed_rule": "fixed-test-seed-rule", "trials_per_cell": len(trial_seeds),
            "duration_months": 12, "python_version": "3.12.test",
            "code_sha256": {"model": "same"},
            "model_conventions": "proposed-2026-10-22",
            "aggregation_conventions": "proposed-test-convention",
            "status": "completed",
            "cells": [{
                "name": "food-4.6_area-50", "food_rabbits_per_ha": 4.6,
                "area_km2_per_patch": 50, "planned_trials": len(trial_seeds),
                "status": "completed", "statistics": statistics,
                "trials": records,
            }],
        }
        paths[rule] = folder / "batch.json"
        write_json(paths[rule], batch)
    return paths


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_comparison_checks_matching_batches_and_renders_side_by_side(tmp_path):
    result = comparison.compare_batches(make_batches(tmp_path))

    assert result["historical_validation"] == "not_assessed"
    assert result["settlement_rules_are_provisional"] is True
    assert len(result["cells"]) == 1
    assert set(result["cells"][0]["rules"]) == set(SETTLEMENT_RULES)
    markdown = comparison.render_markdown(result)
    assert "Monthly: current patch, then other" in markdown
    assert "Monthly: own patch only" in markdown
    assert "One try at dispersal" in markdown
    assert "does not select a rule" in markdown
    assert "95% interval" in markdown


def test_comparison_rejects_a_batch_with_different_seed(tmp_path):
    paths = make_batches(tmp_path)
    path = paths["monthly_own_patch_only"]
    batch = json.loads(path.read_text())
    batch["seed"] = 14
    path.write_text(json.dumps(batch))

    with pytest.raises(ValueError, match="seed differs"):
        comparison.compare_batches(paths)


def test_comparison_rejects_an_incomplete_batch(tmp_path):
    paths = make_batches(tmp_path)
    path = paths["one_try_at_dispersal"]
    batch = json.loads(path.read_text())
    batch["status"] = "incomplete"
    path.write_text(json.dumps(batch))

    with pytest.raises(ValueError, match="not completed"):
        comparison.compare_batches(paths)


def test_comparison_rejects_trial_rule_mismatch(tmp_path):
    paths = make_batches(tmp_path)
    path = paths["monthly_own_patch_only"]
    batch = json.loads(path.read_text())
    artifact = path.parent / batch["cells"][0]["trials"][0]["artifacts"] / "input.json"
    run_input = json.loads(artifact.read_text())
    run_input["settlement_rule"] = DEFAULT_SETTLEMENT_RULE
    artifact.write_text(json.dumps(run_input))

    with pytest.raises(ValueError, match="wrong settlement rule"):
        comparison.compare_batches(paths)


def test_comparison_rejects_invalid_summary_statistics(tmp_path):
    paths = make_batches(tmp_path)
    path = paths["one_try_at_dispersal"]
    batch = json.loads(path.read_text())
    batch["cells"][0]["statistics"]["persistence_share"] = 1.5
    path.write_text(json.dumps(batch))

    with pytest.raises(ValueError, match="out-of-range statistics"):
        comparison.compare_batches(paths)


def test_report_does_not_overwrite_existing_file(tmp_path):
    output = tmp_path / "comparison.md"
    output.write_text("keep this")

    with pytest.raises(FileExistsError):
        comparison.write_report({}, output)

    assert output.read_text() == "keep this"


def test_comparison_accepts_batches_whose_trials_each_have_their_own_seed(tmp_path):
    """A real batch gives every trial its own seed; the three batches must still match trial by trial."""
    paths = make_batches(tmp_path, trial_seeds=(1001, 1002, 1003))

    result = comparison.compare_batches(paths)

    assert result["trials_per_cell"] == 3
    assert set(result["cells"][0]["rules"]) == set(SETTLEMENT_RULES)


def test_comparison_rejects_batches_whose_trial_seeds_differ_between_rules(tmp_path):
    paths = make_batches(tmp_path, trial_seeds=(1001, 1002))
    path = paths["one_try_at_dispersal"]
    batch = json.loads(path.read_text())
    record = batch["cells"][0]["trials"][1]
    record["seed"] = 2002
    folder = path.parent / record["artifacts"]
    for name in ("input.json", "results.json"):
        data = json.loads((folder / name).read_text())
        data["seed"] = 2002
        if name == "results.json":
            data["config"]["seed"] = 2002
        write_json(folder / name, data)
    write_json(path, batch)

    with pytest.raises(ValueError, match="matching trial seeds"):
        comparison.compare_batches(paths)


def test_comparison_rejects_statistics_that_are_in_range_but_not_what_the_trials_give(tmp_path):
    paths = make_batches(tmp_path)
    path = paths["one_try_at_dispersal"]
    batch = json.loads(path.read_text())
    batch["cells"][0]["statistics"]["final_population_median"] = 5  # a valid number; the trial says 20
    path.write_text(json.dumps(batch))

    with pytest.raises(ValueError, match="statistics differ from its trial results"):
        comparison.compare_batches(paths)


def test_report_defines_persistence_and_labels_extinction_time_as_extinct_trials_only(tmp_path):
    markdown = comparison.render_markdown(comparison.compare_batches(make_batches(tmp_path)))

    assert "living breeding-age female holding a territory" in markdown
    assert "Median extinction time (extinct trials only)" in markdown
    assert "not a statistical test of any difference between rules" in markdown
