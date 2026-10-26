"""Eval-plan cases for the Evaluator:  planted malformed inputs, zero food, and a known extinction."""

import copy
import json

import jsonschema
import pytest

from simulation import model
from simulation.model import REPO, preview_config, simulate, summary
from validators.results_checks import build_evaluation

SCHEMA = json.loads((REPO / "schemas" / "evaluation.schema.json").read_text())


def check(evaluation):
    jsonschema.validate(evaluation, SCHEMA)
    return evaluation


def planted(name, change):
    return pytest.param(change, id=name)


def drop(field):
    return lambda c: c.pop(field)


def put(field, value):
    return lambda c: c.__setitem__(field, value)


def stale_table(c):
    c["parameters_sha256"] = "f" * 64


def one_patch(c):
    c["patches"] = c["patches"][:1]


def traversal(c):
    c["parameters_csv"] = "../README.md"


# The ten planted malformed inputs (eval plan, tool-use reliability).  Bar:  10 of 10 are rejected
# before the model runs.
MALFORMED = [
    planted("missing_seed", drop("seed")),
    planted("unknown_field", put("disease_shock", True)),
    planted("zero_duration", put("duration_months", 0)),
    planted("start_month_13", put("start_month", 13)),
    planted("purpose_historical", put("purpose", "historical")),
    planted("stale_table_hash", stale_table),
    planted("path_leaves_the_repository", traversal),
    planted("one_patch_only", one_patch),
    planted("negative_food", put("food_rabbits_per_ha", -1)),
    planted("text_for_food", put("food_rabbits_per_ha", "plenty")),
]


@pytest.mark.parametrize("change", MALFORMED)
def test_each_planted_malformed_input_is_rejected_before_the_model_runs(change, monkeypatch):
    def must_not_run(*args, **kwargs):
        raise AssertionError("the model ran on a malformed input")

    monkeypatch.setattr(model, "run_model", must_not_run)
    config = preview_config(seed=1, months=6)
    change(config)
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        simulate(config)


def test_there_are_ten_planted_malformed_inputs():
    assert len(MALFORMED) == 10


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_zero_food_gives_no_births_and_a_run_the_evaluator_passes(seed):
    config = preview_config(seed=seed, months=120, food=0)
    results = simulate(config)
    history = results["history"]
    assert all(row["births"] == 0 for row in history)
    assert all(row["population"] >= 0 and row["females"] >= 0 and row["males"] >= 0 for row in history)
    assert all(later["population"] <= earlier["population"] for earlier, later in zip(history, history[1:]))
    assert results["persisted"] is False  # every starting animal is past breeding age by month 120
    evaluation = check(build_evaluation(config, results, REPO))
    assert evaluation["status"] == "pass"


def test_zero_food_reports_what_was_observed_about_extinction():
    # The eval plan:  zero food stops births but does not guarantee extinction within 120 months.
    # The report must follow the observed history, and never invent an extinction month.
    for seed in (1, 2, 3):
        results = simulate(preview_config(seed=seed, months=120, food=0))
        history = results["history"]
        first_zero = next((row["month"] for row in history if row["population"] == 0), None)
        assert summary(results)["extinction_month"] == first_zero
        assert (first_zero is None) == (history[-1]["population"] > 0)


def extinct_fixture():
    """A controlled run that reaches population zero at month 3 (hand-built, labeled sample)."""
    config = json.loads((REPO / "examples/handoffs/input.json").read_text())
    results = json.loads((REPO / "examples/handoffs/results.json").read_text())
    config["duration_months"] = 3
    results["config"] = copy.deepcopy(config)
    rows = [(4, 2, 2, 0), (3, 2, 1, 1), (1, 0, 1, 2), (0, 0, 0, 1)]
    results["history"] = [dict(month=m, population=p, females=f, males=ma, births=0, deaths=d, movements=0)
                          for m, (p, f, ma, d) in enumerate(rows)]
    ages = [40, 50, 60, 70]
    results["final_animals"] = [dict(id=f"x-{i}", sex="female" if i < 2 else "male", age_months=age,
                                     patch_id="AB"[i % 2], alive=False, settled=False)
                                for i, age in enumerate(ages)]
    results["persisted"] = False
    return config, results


def test_a_controlled_extinction_is_reported_at_its_known_month_and_passes_the_checks():
    config, results = extinct_fixture()
    assert summary(results)["extinction_month"] == 3
    assert summary(results)["final_population"] == 0
    evaluation = check(build_evaluation(config, results, REPO))
    assert evaluation["status"] == "pass", [c for c in evaluation["checks"] if not c["passed"]]


def test_a_run_that_did_not_go_extinct_reports_no_extinction_month():
    config, results = extinct_fixture()
    results["history"][-1].update(population=1, males=1, deaths=0)
    results["history"][-2].update(population=1, females=0, males=1, deaths=2)
    results["final_animals"][3]["alive"] = True
    results["final_animals"][3]["settled"] = False
    assert summary(results)["extinction_month"] is None


def test_an_extinct_run_that_still_lists_a_living_animal_is_caught():
    config, results = extinct_fixture()
    results["final_animals"][0]["alive"] = True
    evaluation = check(build_evaluation(config, results, REPO))
    assert evaluation["status"] == "revise"
    assert "final_counts" in {c["name"] for c in evaluation["checks"] if not c["passed"]}
