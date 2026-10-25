"""The Evaluator's code checks on one run.

JSON Schema cannot say that a population balances, that a month is missing, or that the
reported persistence matches the final animals.  These checks do, from the input file, the
results file, and the research CSV only.  They do not import the simulator, so the Evaluator
does not trust the Developer's code.  They check the run;  they do not judge the biology.
"""

import argparse
import csv
import json
import math
from pathlib import Path

import jsonschema

from validators.handoff_hashes import check_files_current, check_handoff_hashes

ROOT = Path(__file__).resolve().parents[1]
ZERO_HASH = "0" * 64
MAX_ROUND = 3


def _schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())


def _parameters(run_input, root):
    """The few baseline values the checks need, with the run's overrides applied."""
    rows = {}
    with (Path(root) / run_input["parameters_csv"]).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["name"]] = float(row["baseline"])
    overrides = run_input["parameter_overrides"]
    return dict(
        breeding_min=round(12 * rows["breeding_age_min"]),
        breeding_max=round(12 * rows["breeding_age_max"]),
        birth_month=round(rows["birth_month"]),
        home_range=overrides.get("female_home_range_km2", rows["female_home_range_km2"]),
        food_threshold=overrides.get("rabbit_density_spring_min_for_territorial_breeding",
                                     rows["rabbit_density_spring_min_for_territorial_breeding"]),
    )


def _breeding_age(animal, params):
    return animal["alive"] and params["breeding_min"] <= animal["age_months"] <= params["breeding_max"]


# Each check returns (passed, detail, requested change).  A failed check becomes one issue.

def check_identity(run_input, results, params):
    wrong = [name for name in ("run_id", "seed") if results[name] != run_input[name]]
    if results["config"] != run_input:
        wrong.append("config")
    if wrong:
        return (False, f"results differ from the input in: {', '.join(wrong)}.",
                "Return results that carry the input's run ID, seed, and unchanged configuration.")
    return True, "Run ID, seed, and configuration match the input.", ""


def check_provenance(run_input, results, params):
    placeholders = [field for field in ("parameters_sha256", "sources_sha256")
                    if results["config"][field] == ZERO_HASH]
    if results["data_kind"] == "simulation" and placeholders:
        return (False, "A simulation run carries placeholder (all-zero) file hashes.",
                "Compute the real hashes with validators/handoff_hashes.py, or label the file data_kind sample.")
    return True, f"data_kind {results['data_kind']} fits the hashes.", ""


def check_hashes(run_input, results, params, root=".", **_):
    errors = check_handoff_hashes(run_input, results)
    if results["data_kind"] == "sample":
        detail = "Sample data:  the on-disk hash check is skipped."
    else:
        errors += check_files_current(run_input, root)
        detail = "Both research files match the hashes in the input and the results."
    if errors:
        return (False, "; ".join(errors),
                "Start a new run from a fresh input with the current hashes; a changed research file is not a revision.")
    return True, detail, ""


def check_months(run_input, results, params):
    history = results["history"]
    months = [row["month"] for row in history]
    if months != list(range(run_input["duration_months"] + 1)):
        return (False, f"History months are not 0 to {run_input['duration_months']} without gaps.",
                "Record every month from 0 to the duration, once each, in order.")
    first = history[0]
    if first["births"] or first["deaths"] or first["movements"]:
        return (False, "Month 0 reports births, deaths, or movements.",
                "Report zero births, deaths, and movements in month 0.")
    return True, f"History covers months 0 to {run_input['duration_months']} in order.", ""


def check_accounting(run_input, results, params):
    history = results["history"]
    for row in history:
        if row["females"] + row["males"] != row["population"]:
            return (False, f"Month {row['month']}:  females plus males is not the population.",
                    "Make the sex counts add up to the living population in every month.")
    for before, row in zip(history, history[1:]):
        if row["population"] != before["population"] + row["births"] - row["deaths"]:
            return (False, f"Month {row['month']}:  population is not the last population plus births minus deaths.",
                    "Make births and deaths balance the population in every month.")
    return True, f"Population balances in all {len(history) - 1} months.", ""


def check_animals(run_input, results, params):
    animals = results["final_animals"]
    patches = {patch["id"] for patch in run_input["patches"]}
    if len({a["id"] for a in animals}) != len(animals):
        return False, "Two final animals share an ID.", "Give every animal a unique ID."
    if any(a["patch_id"] not in patches for a in animals):
        return (False, "A final animal sits in a patch that the input does not define.",
                "Use only the patch IDs of the input.")
    if any(a["settled"] and (not a["alive"] or a["sex"] != "female") for a in animals):
        return (False, "A male or a dead animal is marked as holding a territory.",
                "Mark settled only for a living female.")
    return True, f"{len(animals)} final animals have unique IDs, valid patches, and valid territory flags.", ""


def check_capacity(run_input, results, params):
    for patch in run_input["patches"]:
        capacity = math.floor(patch["area_km2"] / params["home_range"])
        held = sum(a["alive"] and a["settled"] and a["patch_id"] == patch["id"]
                   for a in results["final_animals"])
        if held > capacity:
            return (False, f"Patch {patch['id']} holds {held} territories but fits {capacity}.",
                    "Hold at most floor(area / female home range) territories in each patch.")
    return True, "No patch holds more territories than its area allows.", ""


def check_final_counts(run_input, results, params):
    animals = results["final_animals"]
    history = results["history"]
    living = [a for a in animals if a["alive"]]
    females = sum(a["sex"] == "female" for a in living)
    last = history[-1]
    if (last["population"], last["females"], last["males"]) != (len(living), females, len(living) - females):
        return (False, "The last history row does not match the living final animals.",
                "Make the last month's counts equal the living animals in final_animals.")
    created = history[0]["population"] + sum(row["births"] for row in history[1:])
    if len(animals) != created:
        return (False, f"final_animals holds {len(animals)} animals but {created} were created.",
                "List every animal created, including the dead, in final_animals.")
    if len(animals) - len(living) != sum(row["deaths"] for row in history[1:]):
        return (False, "The dead animals do not match the deaths in the history.",
                "Keep every dead animal in final_animals, and report each death once.")
    return True, f"{len(living)} living and {len(animals) - len(living)} dead animals match the history.", ""


def check_birth_timing(run_input, results, params):
    food_enough = run_input["food_rabbits_per_ha"] >= params["food_threshold"]
    for row in results["history"][1:]:
        calendar_month = (run_input["start_month"] - 1 + row["month"]) % 12 + 1
        if row["births"] and calendar_month != params["birth_month"]:
            return (False, f"Month {row['month']} reports births outside the birth month.",
                    "Allow births only in the birth month (March).")
        if row["births"] and not food_enough:
            return (False, f"Month {row['month']} reports births with food below the spring threshold.",
                    "Allow no births when the food density is below the spring threshold.")
    return True, "Births occur only in the birth month and only with enough food.", ""


def check_persistence(run_input, results, params):
    animals = results["final_animals"]
    male_patches = {a["patch_id"] for a in animals if a["sex"] == "male" and _breeding_age(a, params)}
    expected = any(a["sex"] == "female" and a["settled"] and _breeding_age(a, params)
                   and a["patch_id"] in male_patches for a in animals)
    if results["persisted"] != expected:
        return (False, f"persisted is {results['persisted']} but the final animals give {expected}.",
                "Compute persistence from the final animals:  a living breeding-age female holding a territory "
                "and a living breeding-age male in one patch.")
    return True, f"persisted ({expected}) matches the final animals.", ""


CHECKS = (
    ("run_identity", check_identity),
    ("provenance", check_provenance),
    ("file_hashes", check_hashes),
    ("history_months", check_months),
    ("population_accounting", check_accounting),
    ("animal_records", check_animals),
    ("territory_capacity", check_capacity),
    ("final_counts", check_final_counts),
    ("birth_timing_and_food", check_birth_timing),
    ("persistence_recomputed", check_persistence),
)


def _schema_check(name, document, schema_name):
    try:
        jsonschema.validate(document, _schema(schema_name))
    except jsonschema.ValidationError as exc:
        return dict(name=name, passed=False, detail=f"{exc.message} (at {'/'.join(map(str, exc.absolute_path)) or 'top level'})",
                    requested_change=f"Return a {schema_name} file that matches its schema.")
    return dict(name=name, passed=True, detail=f"The {schema_name} file matches its schema.", requested_change="")


def run_checks(run_input, results, root="."):
    """Run every check; return a list of dicts with name, passed, detail, requested_change.

    If a file fails its schema, only the schema checks are returned, because the later checks
    assume the fields exist.
    """
    first = [_schema_check("input_schema", run_input, "input"),
             _schema_check("results_schema", results, "results")]
    if not all(check["passed"] for check in first):
        return first
    params = _parameters(run_input, root)
    checks = list(first)
    for name, function in CHECKS:
        kwargs = dict(root=root) if function is check_hashes else {}
        passed, detail, change = function(run_input, results, params, **kwargs)
        checks.append(dict(name=name, passed=passed, detail=detail, requested_change=change))
    return checks


def build_evaluation(run_input, results, root=".", revision_round=None):
    """The evaluation.json for one run:  pass, revise, or stop (never more than 3 revision rounds)."""
    checks = run_checks(run_input, results, root)
    round_number = results.get("revision_round", 0) if revision_round is None else revision_round
    issues = [dict(code=c["name"], message=c["detail"], requested_change=c["requested_change"])
              for c in checks if not c["passed"]]
    if not issues:
        status = "pass"
    elif round_number >= MAX_ROUND:
        status = "stop"
    else:
        status = "revise"
    return dict(
        schema_version="1.0", run_id=run_input["run_id"],
        data_kind="sample" if results.get("data_kind") == "sample" else "evaluation",
        revision_round=round_number,
        parameters_sha256=run_input["parameters_sha256"], sources_sha256=run_input["sources_sha256"],
        status=status, issues=issues,
        checks=[dict(name=c["name"], passed=c["passed"], detail=c["detail"]) for c in checks],
        historical_validation="not_assessed")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check one run and write its evaluation.json.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new evaluation.json; never overwritten")
    parser.add_argument("--root", type=Path, default=ROOT, help="folder that holds the research files")
    parser.add_argument("--revision-round", type=int, help="defaults to the round in the results file")
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Output file already exists; use a new file name")
        run_input = json.loads(args.input.read_text())
        results = json.loads(args.results.read_text())
        evaluation = build_evaluation(run_input, results, args.root, args.revision_round)
        args.output.write_text(json.dumps(evaluation, indent=2, allow_nan=False) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Evaluation failed: {exc}")
        return 2
    print(f"Evaluation saved to {args.output}.  Status: {evaluation['status']}, "
          f"{len(evaluation['issues'])} issue(s).")
    return 0 if evaluation["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
