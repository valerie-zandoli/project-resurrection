"""The scripted hand-back example:  one batched round, a required gap left open stops the case, and the
files it writes are the ones the fallback bundle expects in `hand-back/`."""

import ast
import importlib.util
import json

import pytest

from harness import handback_example as example
from simulation.model import REPO
from validators.evidence_gate import check_repository

spec = importlib.util.spec_from_file_location("check_fallback", REPO / "scripts" / "check_fallback.py")
fallback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fallback)


def run(tmp_path):
    out = tmp_path / "hand-back"
    case = example.run_example(out)
    return out, case, json.loads((out / "case.json").read_text()), \
        [json.loads(line) for line in (out / "trace.jsonl").read_text().splitlines()]


def test_the_required_gap_left_open_stops_the_case_and_names_both_owners(tmp_path):
    _, _, case, _ = run(tmp_path)
    assert case["status"] == "stop"
    assert "female_home_range_km2" in case["reason"] and "unresolved" in case["reason"]
    assert case["notify"] == ["Valerie", "Anastasiya"]
    assert case["handback"]["round_used"] is True


def test_the_optional_gap_is_a_logged_limitation_and_does_not_stop_the_case(tmp_path):
    _, _, case, _ = run(tmp_path)
    assert any(item.startswith("diet_rabbit_fraction:") for item in case["handback"]["limitations"])
    assert "diet_rabbit_fraction" not in case["reason"]


def test_one_batched_request_holds_both_gaps_with_every_field(tmp_path):
    _, _, case, _ = run(tmp_path)
    requests = case["handback"]["requests"]
    assert [r["parameter"] for r in requests] == ["female_home_range_km2", "diet_rabbit_fraction"]
    assert [r["classification"] for r in requests] == ["required", "optional"]
    assert all(all(str(value).strip() for value in r.values()) for r in requests)


def test_a_second_round_is_refused_and_the_refusal_is_traced(tmp_path):
    _, _, case, trace = run(tmp_path)
    assert case["second_round"].startswith("refused")
    assert any("second round" in line["message"] and "refused" in line["message"] for line in trace)


def test_the_two_gaps_are_real_rows_of_the_research_files(tmp_path):
    # If the table changes so that a gap is no longer weak, this example must be rewritten, not kept.
    refused, evidence = check_repository(REPO, "pilot")
    assert not refused
    assert {"female_home_range_km2", "diet_rabbit_fraction"} <= set(evidence["low"])
    model = (REPO / "simulation" / "model.py").read_text()
    assert "female_home_range_km2" in model and "diet_rabbit_fraction" not in model  # required vs optional


def test_the_files_pass_the_fallback_checks_for_the_hand_back_folder(tmp_path):
    out, _, _, _ = run(tmp_path)
    fallback.check_case_summary(out / "case.json")
    fallback.check_trace(out / "trace.jsonl")


def test_the_example_is_labeled_scripted_everywhere_it_is_shown(tmp_path, capsys):
    out = tmp_path / "cli"
    assert example.main(["--output", str(out)]) == 1  # a stopped case exits 1, like the harness
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == printed[-1] == f"Caption: {example.CAPTION}"
    case = json.loads((out / "case.json").read_text())
    assert case["mode"] == "scripted_handback_example" and case["caption"] == example.CAPTION
    assert json.loads((out / "trace.jsonl").read_text().splitlines()[0])["message"].startswith(example.CAPTION)


def test_an_existing_folder_is_never_overwritten(tmp_path, capsys):
    out = tmp_path / "hand-back"
    example.run_example(out)
    before = (out / "case.json").read_bytes()
    assert example.main(["--output", str(out)]) == 2
    assert (out / "case.json").read_bytes() == before


def test_the_example_calls_no_model_and_opens_no_network():
    tree = ast.parse((REPO / "harness" / "handback_example.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"litellm", "anthropic", "urllib", "http", "socket", "requests", "subprocess"})
