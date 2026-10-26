import json

import pytest

from scripts import compare_settlement_runs as comparison

DEFAULT_SETTLEMENT_RULE = comparison.DEFAULT_SETTLEMENT_RULE
SETTLEMENT_RULES = comparison.SETTLEMENT_RULES


def make_batches(tmp_path):
    paths = {}
    for rule in SETTLEMENT_RULES:
        folder = tmp_path / rule
        trial_dir = folder / "food-4.6_area-50" / "trial-000000"
        trial_dir.mkdir(parents=True)
        run_id = f"preview-{rule}-food-4.6_area-50-000000"
        run_input = {
            "schema_version": "2.1", "run_id": run_id, "seed": 1001,
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
            "run_id": run_id, "seed": 1001, "config": run_input,
        })
        write_json(trial_dir / "summary.json", trial_summary)
        statistics = {
            "trials": 1, "persistence_share": 1.0,
            "persistence_wilson_95": [0.2065, 1.0],
            "final_population_median": 20, "final_population_p10": 20,
            "final_population_p90": 20, "extinction_share": 0.0,
            "extinction_month_median": None,
        }
        batch = {
            "format_version": "preview-batch-1", "purpose": "synthetic_preview",
            "historical_validation": "not_assessed", "settlement_rule": rule,
            "seed": 13, "seed_rule": "fixed-test-seed-rule", "trials_per_cell": 1,
            "duration_months": 12, "python_version": "3.12.test",
            "code_sha256": {"model": "same"},
            "model_conventions": "proposed-2026-10-22",
            "aggregation_conventions": "proposed-test-convention",
            "status": "completed",
            "cells": [{
                "name": "food-4.6_area-50", "food_rabbits_per_ha": 4.6,
                "area_km2_per_patch": 50, "planned_trials": 1,
                "status": "completed", "statistics": statistics,
                "trials": [{
                    "trial": 0, "seed": 1001, "run_id": run_id,
                    "artifacts": "food-4.6_area-50/trial-000000",
                    "status": "completed", **trial_summary,
                }],
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
