"""Build the case folders for planted flaws 1 to 6 of docs/baseline-test.md.

Each flaw is planted in a copy of one valid, real simulator run (the folder `valid`).  Every folder has an
`input.json`, a `results.json` (except flaws 2 and 3, which the pipeline stops before any run), and a `root/` folder
with the research files, so `python -m validators.results_checks --root <case>/root ...` works on it.
The folders are named case-1, case-2, and so on, in a seeded random order, so a name never says which case is
which.  The key file, written beside the output folder and never inside it, maps each folder to its case and holds
the truth and, for each case, what the code checks actually reported when the case was built:  keep it away from
the arms until the scoring step.

Flaws 7 and 8 live in the research files and are built by `scripts/baseline_cases.py`.
"""

import argparse
import copy
import csv
import json
import random
import secrets
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import jsonschema  # noqa: E402

from simulation.model import preview_config, simulate  # noqa: E402
from validators.parameters import validate_parameters  # noqa: E402
from validators.results_checks import _parameters, build_evaluation  # noqa: E402

PARAMETERS = Path("data/parameters/iberian_lynx_baseline.csv")
SOURCES = Path("data/parameters/sources.csv")
MORTALITY = "annual_mortality_rate_all_causes"


def blinded_names(names, seed):
    """Map each real case name to a folder name that does not reveal it:  case-1, case-2, ... in a seeded random order."""
    labels = [f"case-{number}" for number in range(1, len(names) + 1)]
    random.Random(seed).shuffle(labels)
    return dict(zip(names, labels))


def make_root(destination, source_root):
    """Copy the two research files into `destination`, keeping their relative paths."""
    for relative in (PARAMETERS, SOURCES):
        target = Path(destination) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(source_root) / relative, target)
    return Path(destination)


def run(root, seed, months, overrides=None, food=4.6, area=50):
    config = preview_config(seed=seed, months=months, food=food, area=area, root=root)
    if overrides:
        config["parameter_overrides"] = dict(overrides)
    return config, simulate(config, root=root)


def parameter_row(root, name):
    with (Path(root) / PARAMETERS).open(encoding="utf-8-sig", newline="") as handle:
        return next(row for row in csv.DictReader(handle) if row["name"] == name)


def unbalance_one_month(results):
    """Flaw 1: one month reports one more death than the population change allows."""
    flawed = copy.deepcopy(results)
    month = len(flawed["history"]) // 2
    flawed["history"][month]["deaths"] += 1
    return flawed, month


def pair_only_persistence(results, params):
    """The wrong endpoint of flaw 6:  any living breeding-age female and male, ignoring territory and patch."""
    animals = results["final_animals"]
    breeding = lambda a: a["alive"] and params["breeding_min"] <= a["age_months"] <= params["breeding_max"]
    return (any(a["sex"] == "female" and breeding(a) for a in animals)
            and any(a["sex"] == "male" and breeding(a) for a in animals))


def find_wrong_endpoint_run(root, seeds=range(1, 400), months=(24, 60, 120), foods=(1.0, 4.6)):
    """Search for a real run where the pair-only endpoint says True and the agreed endpoint says False."""
    for month_count in months:
        for food in foods:
            for seed in seeds:
                config, results = run(root, seed, month_count, food=food)
                params = _parameters(config, root)
                if not results["persisted"] and pair_only_persistence(results, params):
                    flawed = copy.deepcopy(results)
                    flawed["persisted"] = True
                    return config, flawed
    raise ValueError("no run found where the pair-only endpoint differs from the agreed endpoint")


def plant_history_leakage(report):
    """Flaw 5:  a history report whose calibration used the 2011 count (the held-out target)."""
    flawed = copy.deepcopy(report)
    calibration = flawed["areas"][0]["calibration"]
    calibration["calibration_months"] = 108
    calibration["calibration_target"] = "median 2011 count within the held-out bounds"
    return flawed


def evaluate(config, results, root):
    evaluation = build_evaluation(copy.deepcopy(config), copy.deepcopy(results), root)
    return dict(status=evaluation["status"],
                failed_checks=[check["name"] for check in evaluation["checks"] if not check["passed"]])


def write_case(folder, config, results, source_root):
    folder.mkdir(parents=True)
    make_root(folder / "root", source_root)
    (folder / "input.json").write_text(json.dumps(config, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if results is not None:
        (folder / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _build_cases(output, source_root=REPO, seed=3, months=24, history_report=None):
    """Write the cases under their real names into `output` (a staging folder) and return the key."""
    output = Path(output)
    if output.exists():
        raise ValueError(f"{output} already exists; use a new folder")
    source_root = Path(source_root)
    key = {}
    cases = {}

    valid_config, valid_results = run(source_root, seed, months)
    if not valid_results["history"][months // 2]["births"] and not any(r["births"] for r in valid_results["history"]):
        raise ValueError("the valid run has no births; pick another seed or more months")
    cases["valid"] = (valid_config, valid_results, source_root)

    flawed, month = unbalance_one_month(valid_results)
    cases["flaw1"] = (valid_config, flawed, source_root)
    key["flaw1"] = dict(flaw=1, what=f"month {month} reports one extra death; the population does not move")

    row = parameter_row(source_root, MORTALITY)
    config2 = preview_config(seed=seed, months=months, root=source_root)
    config2["parameter_overrides"] = {MORTALITY: 0.80}
    schema = json.loads((REPO / "schemas" / "input.schema.json").read_text(encoding="utf-8"))
    schema_errors = [error.message for error in jsonschema.Draft202012Validator(schema).iter_errors(config2)]
    try:
        simulate(config2, root=source_root)
        simulator_refuses = False
    except (ValueError, jsonschema.ValidationError):
        simulator_refuses = True
    key["flaw2"] = dict(flaw=2, what=f"input overrides {MORTALITY} to 0.80; the table's published range is "
                                     f"{row['low']} to {row['high']}",
                        input_schema_errors=schema_errors, simulator_refuses_to_run=simulator_refuses)

    with tempfile.TemporaryDirectory() as scratch:
        bad_root = make_root(Path(scratch) / "root", source_root)
        table = (bad_root / PARAMETERS).read_text(encoding="utf-8")
        first = next(csv.DictReader(table.splitlines()))
        (bad_root / PARAMETERS).write_text(table.replace(first["source"], "no_such_source", 1), encoding="utf-8")
        config3 = preview_config(seed=seed, months=months, root=bad_root)
        errors = [error.replace(str(bad_root), "root") for error in
                  validate_parameters(bad_root / PARAMETERS, bad_root / SOURCES)]
        try:
            simulate(config3, root=bad_root)
            simulator_refuses = False
        except ValueError:
            simulator_refuses = True
        flaw3_table = (bad_root / PARAMETERS).read_bytes()
    key["flaw3"] = dict(flaw=3, what=f"row {first['name']} cites the unknown source key 'no_such_source'",
                        parameter_validator_errors=errors, simulator_refuses_to_run=simulator_refuses)

    config, results = run(source_root, seed, months, overrides={MORTALITY: 0.43})
    results["assumptions"] = results["assumptions"] + [
        "Annual mortality 0.43 = all-cause 0.37 raised by the road-traffic share (16.7%) as an extra cause."]
    cases["flaw4"] = (config, results, source_root)
    key["flaw4"] = dict(flaw=4, what="a cause-specific share is added on top of the all-cause mortality "
                                     "(0.37 to 0.43); the table says each share is already inside the all-cause rate")

    config6, results6 = find_wrong_endpoint_run(source_root)
    cases["flaw6"] = (config6, results6, source_root)
    key["flaw6"] = dict(flaw=6, what="persisted is True from the pair-only endpoint; the agreed endpoint needs a "
                                     "living breeding-age female holding a territory and a male in one patch",
                        seed=config6["seed"], months=config6["duration_months"],
                        food=config6["food_rabbits_per_ha"])

    output.mkdir(parents=True)
    for name, (config, results, root) in cases.items():
        write_case(output / name, config, results, source_root)
        key.setdefault(name, dict(flaw=None, what="a valid real run; every check should pass"))
        key[name]["code_checks"] = evaluate(config, results, output / name / "root")

    config2_dir = output / "flaw2"
    config2_dir.mkdir()
    make_root(config2_dir / "root", source_root)
    (config2_dir / "input.json").write_text(json.dumps(config2, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    config3_dir = output / "flaw3"
    config3_dir.mkdir()
    make_root(config3_dir / "root", source_root)
    (config3_dir / "root" / PARAMETERS).write_bytes(flaw3_table)
    config3 = preview_config(seed=seed, months=months, root=config3_dir / "root")
    (config3_dir / "input.json").write_text(json.dumps(config3, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    if history_report is not None:
        report = json.loads(Path(history_report).read_text(encoding="utf-8"))
        folder = output / "flaw5"
        folder.mkdir()
        (folder / "report.json").write_text(json.dumps(plant_history_leakage(report), indent=2, allow_nan=False) + "\n",
                                            encoding="utf-8")
        (output / "valid_report").mkdir()
        (output / "valid_report" / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n",
                                                             encoding="utf-8")
        key["flaw5"] = dict(flaw=5, what="the calibration section says it used 108 months and the 2011 count; "
                                         "a valid report calibrates on 96 months and growth only",
                            code_checks="none:  no code reads a history report yet")
    else:
        key["flaw5"] = dict(flaw=5, what="not built:  no history report was given (--history-report)")

    return key


def build(output, source_root=REPO, seed=3, months=24, history_report=None, key_path=None, blind_seed=None):
    """Build the cases, give every folder a blinded name, and write the key beside the output folder."""
    output = Path(output)
    key_path = Path(key_path) if key_path else output.with_name(output.name + "-key.json")
    if output.exists():
        raise ValueError(f"{output} already exists; use a new folder")
    if key_path.exists():
        raise ValueError(f"{key_path} already exists; use a new file")
    if output.resolve() in key_path.resolve().parents:
        raise ValueError("the key must not be inside the case folder; the arms would see it")
    blind_seed = secrets.randbits(32) if blind_seed is None else blind_seed
    with tempfile.TemporaryDirectory() as scratch:
        stage = Path(scratch) / "cases"
        key = _build_cases(stage, source_root, seed, months, history_report)
        names = sorted(path.name for path in stage.iterdir())
        folders = blinded_names(names, blind_seed)
        output.mkdir(parents=True)
        for name in names:
            shutil.copytree(stage / name, output / folders[name])
    key = {"folders": folders, "blind_seed": blind_seed, **key}
    key_path.write_text(json.dumps(key, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return output, key


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="new folder; never overwritten")
    parser.add_argument("--key", type=Path, help="new key file, outside the output folder (default: <output>-key.json)")
    parser.add_argument("--blind-seed", type=int, help="seed of the folder order (default: random; the key records it)")
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--months", type=int, default=24)
    parser.add_argument("--history-report", type=Path, help="report.json of a history run, the base of flaw 5")
    args = parser.parse_args(argv)
    try:
        out, key = build(args.output, REPO, args.seed, args.months, args.history_report, args.key, args.blind_seed)
    except (OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError) as exc:
        print(f"Baseline cases failed: {exc}")
        return 1
    key_file = args.key or out.with_name(out.name + "-key.json")
    print(f"Cases written to {out} (blinded as case-N); the key is {key_file}:  keep it from the arms.")
    for name in sorted(name for name in key if name not in ("folders", "blind_seed")):
        checks = key[name].get("code_checks")
        if isinstance(checks, dict):
            print(f"  {name}: {checks['status']}, failed checks: {', '.join(checks['failed_checks']) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
