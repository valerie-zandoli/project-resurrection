"""Hash checks keep the three handoffs of one run tied to the same research files."""
import copy
import json
from pathlib import Path

from validators.handoff_hashes import check_files_current, check_handoff_hashes, file_sha256

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "handoffs"


def example(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text())


def run_with_files(tmp_path):
    """An input, results, and evaluation whose hashes match two real files."""
    parameters = tmp_path / "parameters.csv"
    sources = tmp_path / "sources.csv"
    parameters.write_text("name,baseline\nlitter_size,2.5\n")
    sources.write_text("key\npalomares2005\n")
    run_input = example("input")
    run_input["parameters_csv"] = "parameters.csv"
    run_input["sources_csv"] = "sources.csv"
    run_input["parameters_sha256"] = file_sha256(parameters)
    run_input["sources_sha256"] = file_sha256(sources)
    results = example("results")
    results["config"] = copy.deepcopy(run_input)
    evaluation = example("evaluation")
    evaluation["parameters_sha256"] = run_input["parameters_sha256"]
    evaluation["sources_sha256"] = run_input["sources_sha256"]
    return run_input, results, evaluation, parameters


def test_matching_handoffs_pass(tmp_path):
    run_input, results, evaluation, _ = run_with_files(tmp_path)
    assert check_handoff_hashes(run_input, results, evaluation) == []
    assert check_files_current(run_input, tmp_path) == []


def test_evaluation_on_another_table_is_rejected(tmp_path):
    run_input, results, evaluation, _ = run_with_files(tmp_path)
    evaluation["parameters_sha256"] = "1" * 64
    assert check_handoff_hashes(run_input, results, evaluation) == [
        "evaluation.parameters_sha256 differs from the input"
    ]


def test_results_on_another_table_are_rejected(tmp_path):
    run_input, results, evaluation, _ = run_with_files(tmp_path)
    results["config"]["sources_sha256"] = "2" * 64
    assert check_handoff_hashes(run_input, results, evaluation) == [
        "results.config.sources_sha256 differs from the input"
    ]


def test_results_alone_can_be_checked_before_the_evaluation_exists(tmp_path):
    run_input, results, _, _ = run_with_files(tmp_path)
    assert check_handoff_hashes(run_input, results) == []


def test_table_edited_after_the_input_is_rejected(tmp_path):
    run_input, _, _, parameters = run_with_files(tmp_path)
    parameters.write_text("name,baseline\nlitter_size,3.0\n")
    assert check_files_current(run_input, tmp_path) == [
        "parameters.csv: changed since the input recorded its hash"
    ]


def test_missing_file_is_reported_not_raised(tmp_path):
    run_input, _, _, parameters = run_with_files(tmp_path)
    parameters.unlink()
    errors = check_files_current(run_input, tmp_path)
    assert len(errors) == 1 and errors[0].startswith("parameters.csv: cannot read file")


def test_line_endings_do_not_change_the_hash(tmp_path):
    unix = tmp_path / "unix.csv"
    windows = tmp_path / "windows.csv"
    unix.write_bytes(b"a,b\n1,2\n")
    windows.write_bytes(b"a,b\r\n1,2\r\n")
    assert file_sha256(unix) == file_sha256(windows)
