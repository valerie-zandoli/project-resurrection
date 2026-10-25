"""Case files for planted flaws 1 to 6:  what each plant changes, and what the code checks really report."""

import importlib.util
import json
from pathlib import Path

import pytest

from simulation.model import REPO, preview_config, simulate
from validators.handoff_hashes import check_files_current
from validators.results_checks import _parameters

spec = importlib.util.spec_from_file_location("baseline_cases_runs", REPO / "scripts" / "baseline_cases_runs.py")
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)

REPORT = {"run_seed": 1, "areas": [{"main_run": True, "calibration": {
    "trials": 3, "rows": [{"mortality": 0.2, "median_growth": 1.13}], "chosen_mortality": 0.2}}],
    "must_say": ["Three counts are all we hold."]}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    folder = tmp_path_factory.mktemp("cases")
    report = tmp_path_factory.mktemp("report") / "report.json"
    report.write_text(json.dumps(REPORT))
    out, key = cases.build(folder / "out", REPO, history_report=report)
    return out, key


def load(out, case, name):
    return json.loads((out / case / name).read_text())


def test_the_valid_case_passes_every_check(built):
    out, key = built
    assert key["valid"]["code_checks"] == {"status": "pass", "failed_checks": []}
    assert load(out, "valid", "results.json")["persisted"] in (True, False)


def test_flaw1_breaks_the_population_accounting_in_one_month(built):
    out, key = built
    assert key["flaw1"]["code_checks"]["status"] == "revise"
    assert "population_accounting" in key["flaw1"]["code_checks"]["failed_checks"]
    valid, flawed = load(out, "valid", "results.json"), load(out, "flaw1", "results.json")
    changed = [i for i, (a, b) in enumerate(zip(valid["history"], flawed["history"])) if a != b]
    assert len(changed) == 1 and flawed["history"][changed[0]]["deaths"] == valid["history"][changed[0]]["deaths"] + 1


def test_flaw2_is_stopped_by_the_input_schema_before_any_run(built):
    out, key = built
    assert not (out / "flaw2" / "results.json").exists()
    assert load(out, "flaw2", "input.json")["parameter_overrides"] == {"annual_mortality_rate_all_causes": 0.8}
    assert key["flaw2"]["simulator_refuses_to_run"] and "maximum of 0.5" in key["flaw2"]["input_schema_errors"][0]


def test_flaw3_is_stopped_by_the_parameter_validator_with_current_hashes(built):
    out, key = built
    root = out / "flaw3" / "root"
    assert not (out / "flaw3" / "results.json").exists()
    assert "no_such_source" in key["flaw3"]["parameter_validator_errors"][0]
    assert str(out) not in key["flaw3"]["parameter_validator_errors"][0]
    assert key["flaw3"]["simulator_refuses_to_run"]
    # the hashes are current, so the hash check is not what stops this case
    assert check_files_current(load(out, "flaw3", "input.json"), root) == []
    with pytest.raises(ValueError, match="no_such_source"):
        simulate(load(out, "flaw3", "input.json"), root=root)


def test_flaw4_passes_every_code_check_so_only_a_reader_can_catch_it(built):
    out, key = built
    assert key["flaw4"]["code_checks"] == {"status": "pass", "failed_checks": []}
    config, results = load(out, "flaw4", "input.json"), load(out, "flaw4", "results.json")
    assert 0.1 <= config["parameter_overrides"]["annual_mortality_rate_all_causes"] <= 0.5
    assert any("road-traffic share" in line for line in results["assumptions"])


def test_flaw6_is_a_real_run_whose_wrong_endpoint_differs_from_the_agreed_one(built):
    out, key = built
    assert key["flaw6"]["code_checks"]["failed_checks"] == ["persistence_recomputed"]
    config, results = load(out, "flaw6", "input.json"), load(out, "flaw6", "results.json")
    assert results["persisted"] is True
    assert cases.pair_only_persistence(results, _parameters(config, out / "flaw6" / "root"))
    honest = simulate(config, root=out / "flaw6" / "root")
    assert honest["persisted"] is False


def test_flaw5_plants_leakage_in_a_copy_of_the_report_and_leaves_the_valid_one_alone(built):
    out, key = built
    flawed = load(out, "flaw5", "report.json")["areas"][0]["calibration"]
    assert flawed["calibration_months"] == 108 and "2011" in flawed["calibration_target"]
    assert load(out, "valid_report", "report.json") == REPORT
    assert "no code reads a history report" in key["flaw5"]["code_checks"]


def test_every_case_folder_has_a_root_with_the_research_files(built):
    out, _ = built
    for case in ("valid", "flaw1", "flaw2", "flaw3", "flaw4", "flaw6"):
        assert (out / case / "root" / cases.PARAMETERS).exists() and (out / case / "root" / cases.SOURCES).exists()
    assert (out / "valid" / "root" / cases.PARAMETERS).read_bytes() == (REPO / cases.PARAMETERS).read_bytes()


def test_without_a_history_report_flaw5_is_marked_not_built(tmp_path):
    out, key = cases.build(tmp_path / "out", REPO)
    assert "not built" in key["flaw5"]["what"] and not (out / "flaw5").exists()


def test_nothing_is_overwritten_and_no_temporary_folder_is_left(tmp_path):
    cases.build(tmp_path / "out", REPO)
    with pytest.raises(ValueError, match="already exists"):
        cases.build(tmp_path / "out", REPO)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["out"]


def test_the_search_for_a_wrong_endpoint_run_fails_loudly_when_there_is_none():
    with pytest.raises(ValueError, match="no run found"):
        cases.find_wrong_endpoint_run(REPO, seeds=range(1, 2), months=(2,), foods=(4.6,))


def test_the_command_reports_one_line_and_returns_nonzero_on_an_existing_folder(tmp_path, capsys):
    assert cases.main(["--output", str(tmp_path / "out")]) == 0
    assert "flaw1: revise" in capsys.readouterr().out
    assert cases.main(["--output", str(tmp_path / "out")]) == 1
    assert "already exists" in capsys.readouterr().out
