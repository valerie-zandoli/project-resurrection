"""The Evaluator's code checks:  one real run passes, and each planted defect is caught."""

import copy
import json
import shutil

import jsonschema
import pytest

from simulation.model import REPO, preview_config, simulate
from validators.results_checks import build_evaluation, main, run_checks

SCHEMA = json.loads((REPO / "schemas" / "evaluation.schema.json").read_text())


@pytest.fixture(scope="module")
def run():
    config = preview_config(seed=3, months=24, food=4.6, area=50)
    return config, simulate(config)


def evaluate(run_input, results, round_number=None, root=REPO):
    evaluation = build_evaluation(copy.deepcopy(run_input), copy.deepcopy(results), root, round_number)
    jsonschema.validate(evaluation, SCHEMA)
    return evaluation


def failed(evaluation):
    return {check["name"] for check in evaluation["checks"] if not check["passed"]}


def test_a_real_run_passes_every_check(run):
    evaluation = evaluate(*run)
    assert evaluation["status"] == "pass" and evaluation["issues"] == []
    assert len(evaluation["checks"]) == 12
    assert all(check["passed"] for check in evaluation["checks"])
    assert evaluation["data_kind"] == "evaluation"
    assert evaluation["historical_validation"] == "not_assessed"
    assert evaluation["parameters_sha256"] == run[0]["parameters_sha256"]


def test_the_run_has_births_so_the_birth_checks_are_exercised(run):
    assert sum(row["births"] for row in run[1]["history"]) > 0


def test_the_sample_files_pass_with_the_disk_check_skipped():
    config = json.loads((REPO / "examples/handoffs/input.json").read_text())
    results = json.loads((REPO / "examples/handoffs/results.json").read_text())
    evaluation = evaluate(config, results)
    assert evaluation["status"] == "pass" and evaluation["data_kind"] == "sample"
    hashes = next(c for c in evaluation["checks"] if c["name"] == "file_hashes")
    assert "skipped" in hashes["detail"]


def mutate(function):
    def build(run):
        config, results = copy.deepcopy(run[0]), copy.deepcopy(run[1])
        function(config, results)
        return config, results
    return build


def swap_seed(config, results):
    results["seed"] += 1


def change_config(config, results):
    results["config"]["food_rabbits_per_ha"] = 1.0


def zero_hashes(config, results):
    config["parameters_sha256"] = results["config"]["parameters_sha256"] = "0" * 64


def drop_a_month(config, results):
    del results["history"][5]


def month_zero_births(config, results):
    results["history"][0]["births"] = 1
    results["history"][0]["population"] += 1


def unbalanced(config, results):
    results["history"][7]["population"] += 1
    results["history"][7]["females"] += 1


def duplicate_id(config, results):
    results["final_animals"][1]["id"] = results["final_animals"][0]["id"]


def unknown_patch(config, results):
    results["final_animals"][0]["patch_id"] = "Z"


def settled_male(config, results):
    male = next(a for a in results["final_animals"] if a["sex"] == "male" and a["alive"])
    male["settled"] = True


def over_capacity(config, results):
    females = [a for a in results["final_animals"] if a["sex"] == "female" and a["alive"]]
    assert len(females) > 5
    for animal in females:
        animal["patch_id"], animal["settled"] = config["patches"][0]["id"], True


def resurrect(config, results):
    dead = next(a for a in results["final_animals"] if not a["alive"])
    dead["alive"] = True


def flip_persistence(config, results):
    results["persisted"] = not results["persisted"]


def births_in_february(config, results):
    results["history"][1]["births"] += 1
    for row in results["history"][1:]:
        row["population"] += 1
        row["females"] += 1


CASES = [
    ("run_identity", swap_seed),
    ("run_identity", change_config),
    ("provenance", zero_hashes),
    ("history_months", drop_a_month),
    ("history_months", month_zero_births),
    ("population_accounting", unbalanced),
    ("animal_records", duplicate_id),
    ("animal_records", unknown_patch),
    ("territory_capacity", over_capacity),
    ("final_counts", resurrect),
    ("persistence_recomputed", flip_persistence),
    ("birth_timing_and_food", births_in_february),
]


@pytest.mark.parametrize("check, function", CASES, ids=[f"{c}-{f.__name__}" for c, f in CASES])
def test_each_planted_defect_is_caught_by_its_check(run, check, function):
    # A schema-valid change is only a defect for the Evaluator, so the schema checks must still pass.
    evaluation = evaluate(*mutate(function)(run))
    assert check in failed(evaluation)
    assert evaluation["status"] == "revise"
    issue = next(i for i in evaluation["issues"] if i["code"] == check)
    assert issue["message"] and issue["requested_change"]
    assert not {"input_schema", "results_schema"} & failed(evaluation)


def test_food_below_the_threshold_forbids_births():
    config = preview_config(seed=3, months=24, food=4.6, area=50)
    results = simulate(config)
    config["food_rabbits_per_ha"] = results["config"]["food_rabbits_per_ha"] = 1.0
    assert "birth_timing_and_food" in failed(evaluate(config, results))


def test_a_changed_research_file_is_caught_on_disk(tmp_path):
    for relative in ("data/parameters/iberian_lynx_baseline.csv", "data/parameters/sources.csv"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / relative, target)
    config = preview_config(seed=1, months=12, root=tmp_path)
    results = simulate(config, root=tmp_path)
    assert evaluate(config, results, root=tmp_path)["status"] == "pass"
    table = tmp_path / "data/parameters/iberian_lynx_baseline.csv"
    table.write_text(table.read_text().replace("breeding_age_min,3,", "breeding_age_min,4,"))
    evaluation = evaluate(config, results, root=tmp_path)
    assert "file_hashes" in failed(evaluation) and evaluation["status"] == "revise"


def test_revision_rounds_end_in_stop_after_round_3(run):
    broken = mutate(flip_persistence)(run)
    assert [evaluate(*broken, round_number=n)["status"] for n in range(4)] == ["revise", "revise", "revise", "stop"]
    assert evaluate(*run, round_number=3)["status"] == "pass"


def test_the_evaluation_uses_the_rounds_of_the_results(run):
    config, results = copy.deepcopy(run[0]), copy.deepcopy(run[1])
    results["revision_round"] = 2
    assert evaluate(config, results)["revision_round"] == 2


def test_a_schema_failure_returns_only_the_schema_checks_and_does_not_crash(run):
    config, results = copy.deepcopy(run[0]), copy.deepcopy(run[1])
    del results["history"]
    checks = run_checks(config, results, REPO)
    assert [c["name"] for c in checks] == ["input_schema", "results_schema"]
    assert not checks[1]["passed"] and "history" in checks[1]["detail"]
    evaluation = evaluate(config, results)
    assert evaluation["status"] == "revise" and failed(evaluation) == {"results_schema"}


def test_a_settled_male_is_rejected_by_the_schema_and_by_the_code_check(run):
    config, results = mutate(settled_male)(run)
    evaluation = evaluate(config, results)
    assert "results_schema" in failed(evaluation) and evaluation["status"] == "revise"
    # The code check does not rely on the schema:  call it on its own.
    from validators.results_checks import check_animals
    assert check_animals(config, results, {})[0] is False


def test_checks_do_not_import_the_simulator():
    import ast
    tree = ast.parse((REPO / "validators" / "results_checks.py").read_text())
    imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom) and node.module}
    assert "simulation" not in imported


def test_command_line_writes_an_evaluation_and_reports_the_status(run, tmp_path, capsys):
    config, results = run
    (tmp_path / "input.json").write_text(json.dumps(config))
    (tmp_path / "results.json").write_text(json.dumps(results))
    base = ["--input", str(tmp_path / "input.json"), "--results", str(tmp_path / "results.json")]
    assert main(base + ["--output", str(tmp_path / "evaluation.json")]) == 0
    saved = json.loads((tmp_path / "evaluation.json").read_text())
    jsonschema.validate(saved, SCHEMA)
    assert saved["status"] == "pass"
    assert "Status: pass" in capsys.readouterr().out
    # An existing file is never overwritten.
    assert main(base + ["--output", str(tmp_path / "evaluation.json")]) == 2
    bad = copy.deepcopy(results)
    bad["persisted"] = not bad["persisted"]
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    assert main(["--input", str(tmp_path / "input.json"), "--results", str(tmp_path / "bad.json"),
                 "--output", str(tmp_path / "bad-evaluation.json")]) == 1
    assert json.loads((tmp_path / "bad-evaluation.json").read_text())["status"] == "revise"
    assert main(base[:2] + ["--results", str(tmp_path / "missing.json"), "--output", str(tmp_path / "x.json")]) == 2


def legacy_input(config):
    """The same input written as a version 2.0 file, which has no settlement rule."""
    old = copy.deepcopy(config)
    old["schema_version"] = "2.0"
    old.pop("settlement_rule")
    return old


def test_a_version_2_0_input_passes_when_the_simulator_upgraded_it_with_the_default_rule():
    old = legacy_input(preview_config(seed=3, months=24, food=4.6, area=50))
    evaluation = evaluate(old, simulate(old))
    assert evaluation["status"] == "pass", evaluation["issues"]


def test_a_version_2_0_input_still_fails_identity_if_the_results_ran_another_settlement_rule():
    config = preview_config(seed=3, months=24, food=4.6, area=50, settlement_rule="one_try_at_dispersal")
    results = simulate(config)
    old = legacy_input(config)
    assert "run_identity" in failed(evaluate(old, results))


def test_a_version_2_0_input_still_fails_identity_if_anything_else_changed():
    old = legacy_input(preview_config(seed=3, months=24, food=4.6, area=50))
    results = simulate(old)
    results["config"]["food_rabbits_per_ha"] = 55.0
    assert "run_identity" in failed(evaluate(old, results))


def test_the_evaluator_names_the_same_default_settlement_rule_as_the_simulator():
    # The Evaluator writes the default out so that it does not import the simulator; this keeps the two equal.
    from simulation.model import DEFAULT_SETTLEMENT_RULE
    from validators import results_checks
    assert results_checks.DEFAULT_SETTLEMENT_RULE == DEFAULT_SETTLEMENT_RULE
