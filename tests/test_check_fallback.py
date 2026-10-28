"""Tests for scripts/check_fallback.py.  The fixtures are written by hand:  no simulation, no model, and no run of the
history test (its seed is pre-registered, so no test runs it).
"""

import ast
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_fallback", REPO / "scripts" / "check_fallback.py")
fallback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fallback)

FOODS_AREAS = [f"food-{food}_area-{area}" for food in (1, 4.6, 55) for area in (50, 100)]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def batch(trials, status="completed", stage="final"):
    cells = [dict(name=name, status="completed", planned_trials=trials,
                  trials=[dict(trial=n, status="completed") for n in range(trials)]) for name in FOODS_AREAS]
    return dict(format_version="preview-batch-1", status=status, stage=stage, cells=cells)


def trace_lines(count=4):
    return "\n".join(json.dumps(dict(step=n, role="harness", message=f"step {n}")) for n in range(1, count + 1)) + "\n"


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "fallback"
    write_json(root / "history/report.json", dict(
        run_seed=20261101, verdict=dict(result="fail"), areas=[dict(main_run=True), dict(main_run=False)],
        must_say=["a"] * 8, parameters_sha256="0" * 64))
    write_json(root / "batches/pilot/batch.json", batch(100, stage="pilot"))
    write_json(root / "batches/final/batch.json", batch(500, stage="final"))
    (root / "batches/final/table1.md").write_text("| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
    (root / "batches/final/figure1.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
    for name in ("input", "results", "evaluation"):
        (root / "case").mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / "examples" / "handoffs" / f"{name}.json", root / "case" / f"{name}.json")
    write_json(root / "case/case.json", dict(status="pass"))
    (root / "case/trace.jsonl").write_text(trace_lines(), encoding="utf-8")
    write_json(root / "hand-back/case.json", dict(status="stop"))
    (root / "hand-back/trace.jsonl").write_text(trace_lines(), encoding="utf-8")
    (root / "deck").mkdir()
    (root / "deck/design-plan.pdf").write_bytes(b"%PDF-1.4\n" + b"0" * 5000)
    return root


def statuses(root, **kwargs):
    return {item: (status, detail) for item, status, detail in fallback.run_checks(root, **kwargs)}


def only_problem(root, **kwargs):
    problems = {item: (status, detail) for item, (status, detail) in statuses(root, **kwargs).items() if status != "OK"}
    return problems


def test_a_complete_bundle_has_every_item_ok_and_exits_0(bundle, capsys):
    assert only_problem(bundle) == {}
    assert fallback.main(["--root", str(bundle)]) == 0
    assert "items are ready.  Nothing was changed." in capsys.readouterr().out


@pytest.mark.parametrize("key", list(fallback.LAYOUT))
def test_each_missing_file_is_reported_by_name(bundle, key):
    (bundle / fallback.LAYOUT[key]).unlink()
    problems = only_problem(bundle)
    assert problems[fallback.LAYOUT[key]][0] == "MISSING"


def test_an_empty_file_counts_as_missing(bundle):
    (bundle / "history/report.json").write_text("", encoding="utf-8")
    assert only_problem(bundle)["history/report.json"][0] == "MISSING"


def test_a_history_report_with_another_seed_is_bad(bundle):
    report = json.loads((bundle / "history/report.json").read_text())
    report["run_seed"] = 99
    write_json(bundle / "history/report.json", report)
    status, detail = only_problem(bundle)["history/report.json"]
    assert status == "BAD" and "20261101" in detail


def test_a_history_report_without_a_verdict_is_bad(bundle):
    report = json.loads((bundle / "history/report.json").read_text())
    del report["verdict"]
    write_json(bundle / "history/report.json", report)
    assert only_problem(bundle)["history/report.json"][0] == "BAD"


def test_invalid_json_is_bad_with_the_reason(bundle):
    (bundle / "case/results.json").write_text("{not json", encoding="utf-8")
    status, detail = only_problem(bundle)["case/results.json"]
    assert status == "BAD" and "not valid JSON" in detail


@pytest.mark.parametrize("folder, wrong, expected", [("pilot", 50, 100), ("final", 100, 500)])
def test_a_batch_with_the_wrong_trial_count_is_bad(bundle, folder, wrong, expected):
    write_json(bundle / f"batches/{folder}/batch.json", batch(wrong))
    status, detail = only_problem(bundle)[f"batches/{folder}/batch.json"]
    assert status == "BAD" and f"expected {expected}" in detail


def test_the_pilot_is_not_accepted_as_the_final_grid(bundle):
    write_json(bundle / "batches/final/batch.json", batch(100))
    assert only_problem(bundle)["batches/final/batch.json"][0] == "BAD"


def test_an_incomplete_batch_or_cell_is_bad(bundle):
    data = batch(100)
    data["cells"][2]["status"] = "incomplete"
    write_json(bundle / "batches/pilot/batch.json", data)
    status, detail = only_problem(bundle)["batches/pilot/batch.json"]
    assert status == "BAD" and "incomplete" in detail
    write_json(bundle / "batches/pilot/batch.json", batch(100, status="running"))
    assert only_problem(bundle)["batches/pilot/batch.json"][0] == "BAD"


def test_a_failed_trial_makes_the_batch_bad(bundle):
    data = batch(100)
    data["cells"][0]["trials"][3]["status"] = "failed"
    write_json(bundle / "batches/pilot/batch.json", data)
    assert only_problem(bundle)["batches/pilot/batch.json"][0] == "BAD"


def test_a_grid_with_the_wrong_number_of_cells_is_bad(bundle):
    data = batch(100)
    data["cells"] = data["cells"][:5]
    write_json(bundle / "batches/pilot/batch.json", data)
    assert "5 cells" in only_problem(bundle)["batches/pilot/batch.json"][1]


def test_a_trace_with_key_like_text_is_bad(bundle):
    lines = trace_lines().splitlines()
    lines[1] = json.dumps(dict(step=2, role="harness", message="sk-" + "a" * 24))
    (bundle / "case/trace.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    status, detail = only_problem(bundle)["case/trace.jsonl"]
    assert status == "BAD" and "key-like" in detail


def test_a_trace_with_a_skipped_step_or_a_short_trace_is_bad(bundle):
    (bundle / "case/trace.jsonl").write_text(
        json.dumps(dict(step=1, role="a")) + "\n" + json.dumps(dict(step=3, role="a")) + "\n"
        + json.dumps(dict(step=4, role="a")) + "\n", encoding="utf-8")
    assert only_problem(bundle)["case/trace.jsonl"][0] == "BAD"
    (bundle / "hand-back/trace.jsonl").write_text(trace_lines(2), encoding="utf-8")
    assert only_problem(bundle)["hand-back/trace.jsonl"][0] == "BAD"


def test_a_case_summary_with_another_status_is_bad(bundle):
    write_json(bundle / "case/case.json", dict(status="maybe"))
    assert only_problem(bundle)["case/case.json"][0] == "BAD"


def test_results_and_evaluation_of_different_runs_are_bad(bundle):
    evaluation = json.loads((bundle / "case/evaluation.json").read_text())
    evaluation["run_id"] = "another-run"
    write_json(bundle / "case/evaluation.json", evaluation)
    status, detail = only_problem(bundle)["case/ (input, results, evaluation agree)"]
    assert status == "BAD" and "run IDs differ" in detail


def test_an_evaluation_that_names_other_research_files_is_bad(bundle):
    evaluation = json.loads((bundle / "case/evaluation.json").read_text())
    evaluation["parameters_sha256"] = "f" * 64
    write_json(bundle / "case/evaluation.json", evaluation)
    status, detail = only_problem(bundle)["case/ (input, results, evaluation agree)"]
    assert status == "BAD" and "parameters_sha256" in detail


def test_a_file_that_is_not_a_pdf_is_bad_and_no_pdf_is_missing(bundle):
    (bundle / "deck/design-plan.pdf").write_bytes(b"not a pdf" * 400)
    assert only_problem(bundle)["deck/*.pdf"][0] == "BAD"
    (bundle / "deck/design-plan.pdf").unlink()
    assert only_problem(bundle)["deck/*.pdf"][0] == "MISSING"


def test_a_folder_that_does_not_exist_exits_2(tmp_path, capsys):
    assert fallback.main(["--root", str(tmp_path / "nothing")]) == 2
    assert "is not a folder" in capsys.readouterr().err


def test_an_incomplete_bundle_exits_1_and_lists_what_is_missing(bundle, capsys):
    (bundle / "case/trace.jsonl").unlink()
    assert fallback.main(["--root", str(bundle)]) == 1
    out = capsys.readouterr().out
    assert "MISSING case/trace.jsonl" in out and "items are ready" in out


def test_the_checker_changes_nothing(bundle):
    def snapshot():
        return {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(bundle.rglob("*")) if p.is_file()}

    before = snapshot()
    fallback.run_checks(bundle)
    fallback.main(["--root", str(bundle)])
    assert snapshot() == before


def test_the_checker_imports_no_network_or_model_library_and_never_runs_the_history_test():
    tree = ast.parse((REPO / "scripts" / "check_fallback.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"urllib", "http", "socket", "requests", "anthropic", "litellm", "simulation", "subprocess"})
    assert imported <= {"argparse", "json", "re", "sys", "pathlib", "validators"}, imported


@pytest.mark.parametrize("stage, expected", [("pilot", "BAD"), (None, "BAD"), ("final", "OK")])
def test_the_final_grid_must_have_run_at_the_final_stage(bundle, stage, expected):
    # A 500-trial batch run with --stage pilot only warned at the evidence gate, so it is not the final grid.
    data = batch(500, stage=stage)
    if stage is None:
        del data["stage"]  # a batch made before the stage was recorded
    write_json(bundle / "batches/final/batch.json", data)
    assert statuses(bundle)["batches/final/batch.json"][0] == expected


@pytest.mark.parametrize("stage, expected", [("pilot", "OK"), ("final", "OK"), (None, "BAD")])
def test_the_pilot_grid_may_have_run_at_either_stage_but_must_say_which(bundle, stage, expected):
    data = batch(100, stage=stage)
    if stage is None:
        del data["stage"]
    write_json(bundle / "batches/pilot/batch.json", data)
    assert statuses(bundle)["batches/pilot/batch.json"][0] == expected
