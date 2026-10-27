"""Compare completed preview batches that differ only by settlement rule.

Example (run from the repository root):

    python scripts/compare_settlement_runs.py \\
        --monthly batch-monthly/batch.json \\
        --own-patch batch-own/batch.json \\
        --one-try batch-one-try/batch.json \\
        --output settlement-comparison.md

This is a descriptive comparison of provisional model settings. It does not
select or validate a biological rule.
"""

import argparse
import json
import math
from pathlib import Path

DEFAULT_SETTLEMENT_RULE = "monthly_current_then_other"
SETTLEMENT_RULES = (
    DEFAULT_SETTLEMENT_RULE,
    "monthly_own_patch_only",
    "one_try_at_dispersal",
)

RULE_LABELS = {
    DEFAULT_SETTLEMENT_RULE: "Monthly: current patch, then other",
    "monthly_own_patch_only": "Monthly: own patch only",
    "one_try_at_dispersal": "One try at dispersal",
}
COMMON_FIELDS = (
    "format_version", "purpose", "historical_validation", "seed", "seed_rule",
    "trials_per_cell", "duration_months", "python_version", "code_sha256",
    "model_conventions", "aggregation_conventions",
)
STAT_FIELDS = (
    "persistence_share", "persistence_wilson_95", "final_population_median",
    "extinction_share", "extinction_month_median",
)
TRIAL_SUMMARY_FIELDS = (
    "run_id", "persisted", "final_population", "extinction_month",
    "births_final_12_months", "historical_validation", "model_conventions",
)


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc


def _safe_artifact_path(batch_dir, relative):
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe trial artifact path: {relative}")
    resolved = (batch_dir / relative_path).resolve()
    if not resolved.is_relative_to(batch_dir.resolve()):
        raise ValueError(f"Trial artifact escapes its batch folder: {relative}")
    return resolved


def _normalized_input(config):
    """Remove batch-specific identity and the one intended sensitivity axis."""
    normalized = dict(config)
    normalized.pop("run_id", None)
    normalized.pop("seed", None)  # each trial has its own seed; trial seeds are compared across the batches
    normalized.pop("settlement_rule", None)
    return normalized


def _load_batch(path, expected_rule):
    path = Path(path)
    batch = _read_json(path)
    if not isinstance(batch, dict) or batch.get("format_version") != "preview-batch-1":
        raise ValueError(f"{path}: expected a preview-batch-1 manifest")
    if batch.get("status") != "completed":
        raise ValueError(f"{path}: batch is {batch.get('status')!r}, not completed")
    if batch.get("historical_validation") != "not_assessed":
        raise ValueError(f"{path}: expected historical_validation to remain not_assessed")
    if batch.get("settlement_rule") != expected_rule:
        raise ValueError(
            f"{path}: expected settlement rule {expected_rule!r}, "
            f"found {batch.get('settlement_rule')!r}"
        )
    if not isinstance(batch.get("cells"), list) or not batch["cells"]:
        raise ValueError(f"{path}: no batch cells were recorded")

    cells = {}
    for cell in batch["cells"]:
        name = cell.get("name")
        if not isinstance(name, str) or not name or name in cells:
            raise ValueError(f"{path}: missing or duplicate cell name")
        planned = cell.get("planned_trials")
        trials = cell.get("trials")
        cell_stats = cell.get("statistics")
        if (cell.get("status") != "completed" or not isinstance(planned, int)
                or isinstance(planned, bool) or planned < 1 or not isinstance(trials, list)
                or planned != batch.get("trials_per_cell") or len(trials) != planned
                or not isinstance(cell_stats, dict) or cell_stats.get("trials") != planned
                or not all(field in cell_stats for field in STAT_FIELDS)):
            raise ValueError(f"{path}: cell {name!r} is incomplete")
        for field in ("persistence_share", "final_population_median", "extinction_share"):
            value = cell_stats[field]
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(value)):
                raise ValueError(f"{path}: cell {name!r} has invalid {field}")
        if not (0 <= cell_stats["persistence_share"] <= 1
                and 0 <= cell_stats["extinction_share"] <= 1
                and cell_stats["final_population_median"] >= 0):
            raise ValueError(f"{path}: cell {name!r} has out-of-range statistics")
        interval = cell_stats["persistence_wilson_95"]
        if (not isinstance(interval, list) or len(interval) != 2
                or any(not isinstance(value, (int, float)) or isinstance(value, bool)
                       or not math.isfinite(value) for value in interval)
                or not 0 <= interval[0] <= interval[1] <= 1):
            raise ValueError(f"{path}: cell {name!r} has an invalid persistence interval")
        extinction_month = cell_stats["extinction_month_median"]
        if (extinction_month is not None
                and (not isinstance(extinction_month, (int, float))
                     or isinstance(extinction_month, bool) or not math.isfinite(extinction_month)
                     or extinction_month < 0)):
            raise ValueError(f"{path}: cell {name!r} has an invalid extinction month")
        for index, record in enumerate(trials):
            if (record.get("status") != "completed" or record.get("trial") != index
                    or not isinstance(record.get("artifacts"), str)):
                raise ValueError(f"{path}: cell {name!r} has an incomplete trial {index}")
            artifact_dir = _safe_artifact_path(path.parent, record["artifacts"])
            run_input = _read_json(artifact_dir / "input.json")
            results = _read_json(artifact_dir / "results.json")
            summary = _read_json(artifact_dir / "summary.json")
            config = results.get("config")
            if not isinstance(config, dict):
                raise ValueError(f"{path}: trial {index} in {name!r} has no results config")
            if (run_input.get("settlement_rule") != expected_rule
                    or config.get("settlement_rule") != expected_rule):
                raise ValueError(f"{path}: trial {index} in {name!r} has the wrong settlement rule")
            if config != run_input or results.get("run_id") != run_input.get("run_id"):
                raise ValueError(f"{path}: trial {index} in {name!r} results do not match its input")
            if (run_input.get("seed") != record.get("seed")
                    or results.get("seed") != record.get("seed")
                    or run_input.get("run_id") != record.get("run_id")):
                raise ValueError(f"{path}: trial {index} in {name!r} identity does not match its manifest")
            if (run_input.get("food_rabbits_per_ha") != cell.get("food_rabbits_per_ha")
                    or not isinstance(run_input.get("patches"), list)
                    or len(run_input["patches"]) != 2
                    or any(patch.get("area_km2") != cell.get("area_km2_per_patch")
                           for patch in run_input["patches"])):
                raise ValueError(f"{path}: trial {index} in {name!r} does not match its cell settings")
            if any(record.get(key) != summary.get(key) for key in TRIAL_SUMMARY_FIELDS):
                raise ValueError(f"{path}: trial {index} in {name!r} summary differs from its manifest")
            if (type(summary.get("persisted")) is not bool
                    or not isinstance(summary.get("final_population"), (int, float))
                    or isinstance(summary.get("final_population"), bool)
                    or not math.isfinite(summary["final_population"])):
                raise ValueError(f"{path}: trial {index} in {name!r} has invalid summary values")

            baseline = cells.setdefault(name, {"cell": cell, "trials": []})
            comparable = _normalized_input(run_input)
            if index == 0:
                baseline["input"] = comparable
            elif comparable != baseline["input"]:
                raise ValueError(f"{path}: trial inputs differ within cell {name!r}")
            baseline["trials"].append(record)

    return batch, cells


def compare_batches(batch_paths):
    """Return validated descriptive summaries for all three settlement rules."""
    if set(batch_paths) != set(SETTLEMENT_RULES):
        raise ValueError("Provide exactly one completed batch for each of the three settlement rules")
    batches = {rule: _load_batch(batch_paths[rule], rule) for rule in SETTLEMENT_RULES}
    first_rule = SETTLEMENT_RULES[0]
    reference, reference_cells = batches[first_rule]

    for rule, (batch, cells) in batches.items():
        for field in COMMON_FIELDS:
            if batch.get(field) != reference.get(field):
                raise ValueError(f"Batches do not match: {field} differs for {RULE_LABELS[rule]}")
        if set(cells) != set(reference_cells):
            raise ValueError(f"Batches do not contain the same cells: {RULE_LABELS[rule]}")
        for name, cell_data in cells.items():
            reference_cell = reference_cells[name]["cell"]
            for field in ("food_rabbits_per_ha", "area_km2_per_patch", "planned_trials"):
                if cell_data["cell"].get(field) != reference_cell.get(field):
                    raise ValueError(f"Batches do not match: {name} {field} differs")
            if cell_data["input"] != reference_cells[name]["input"]:
                raise ValueError(f"Batches differ in run inputs beyond settlement rule for {name}")
            if [row["seed"] for row in cell_data["trials"]] != [
                    row["seed"] for row in reference_cells[name]["trials"]]:
                raise ValueError(f"Batches do not use matching trial seeds for {name}")

    cells_out = []
    for name, data in reference_cells.items():
        item = {
            "name": name,
            "food_rabbits_per_ha": data["cell"]["food_rabbits_per_ha"],
            "area_km2_per_patch": data["cell"]["area_km2_per_patch"],
            "rules": {},
        }
        for rule in SETTLEMENT_RULES:
            item["rules"][rule] = dict(batches[rule][1][name]["cell"]["statistics"])
        cells_out.append(item)

    return {
        "format_version": "settlement-comparison-1",
        "purpose": "synthetic_preview_comparison",
        "historical_validation": "not_assessed",
        "settlement_rules_are_provisional": True,
        "seed": reference["seed"],
        "seed_rule": reference["seed_rule"],
        "trials_per_cell": reference["trials_per_cell"],
        "duration_months": reference["duration_months"],
        "python_version": reference["python_version"],
        "code_sha256": reference["code_sha256"],
        "cells": cells_out,
    }


def _fmt_pct(value):
    return f"{value:.1%}"


def render_markdown(comparison):
    lines = [
        "# Settlement sensitivity comparison",
        "",
        "> Descriptive comparison of synthetic preview runs. Settlement rules are provisional;",
        "> this report does not select a rule or establish which rule real lynx follow.",
        "",
        (f"Seed: {comparison['seed']} · Trials per cell: {comparison['trials_per_cell']} · "
         f"Months: {comparison['duration_months']} · Python: {comparison['python_version']}"),
        "",
        "Each result lists the persistence share and its 95% Wilson interval, median final population, ",
        "extinction share, and median extinction month (shown as ‘not extinct’ when no trial went extinct).",
        "",
        "| Scenario | Monthly: current patch, then other | Monthly: own patch only | One try at dispersal |",
        "|---|---|---|---|",
    ]
    for cell in comparison["cells"]:
        scenario = (f"{cell['name']}<br>Food {cell['food_rabbits_per_ha']:g} rabbits/ha; "
                    f"area {cell['area_km2_per_patch']:g} km² per patch")
        values = []
        for rule in SETTLEMENT_RULES:
            stats = cell["rules"][rule]
            low, high = stats["persistence_wilson_95"]
            extinction_month = stats["extinction_month_median"]
            extinct_at = "not extinct" if extinction_month is None else f"month {extinction_month:g}"
            values.append(
                f"Persistence: {_fmt_pct(stats['persistence_share'])} "
                f"(95% interval {_fmt_pct(low)}–{_fmt_pct(high)})<br>"
                f"Median final population: {stats['final_population_median']:g}<br>"
                f"Extinction share: {_fmt_pct(stats['extinction_share'])}<br>"
                f"Median extinction time: {extinct_at}"
            )
        lines.append(f"| {scenario} | {values[0]} | {values[1]} | {values[2]} |")
    lines.extend(["", "Historical validation: **not assessed**.", ""])
    return "\n".join(lines)


def write_report(comparison, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(comparison))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--monthly", type=Path, required=True,
                        help="batch.json using monthly_current_then_other")
    parser.add_argument("--own-patch", type=Path, required=True,
                        help="batch.json using monthly_own_patch_only")
    parser.add_argument("--one-try", type=Path, required=True,
                        help="batch.json using one_try_at_dispersal")
    parser.add_argument("--output", type=Path, required=True,
                        help="new Markdown report path; existing files are never overwritten")
    args = parser.parse_args(argv)
    paths = {
        DEFAULT_SETTLEMENT_RULE: args.monthly,
        "monthly_own_patch_only": args.own_patch,
        "one_try_at_dispersal": args.one_try,
    }
    try:
        comparison = compare_batches(paths)
        write_report(comparison, args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Settlement comparison failed: {exc}")
        return 1
    print(f"Comparison report written to {args.output}")
    print("Historical validation: not assessed; no settlement rule selected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
