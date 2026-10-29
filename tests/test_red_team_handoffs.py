"""Red team of our own handoffs and shared state (LaNice's exercise of 2026-10-29; docs/red-team-2026-10-29.md).

Each test feeds malformed input to one component and pins what the harness does.  The last two tests pin two known gaps,
named as such, so that a fix shows up as a change here.  No key or network."""

import os
import shutil
import stat
from pathlib import Path

import pytest

from harness.run_case import run_case, simulator_developer
from simulation.model import REPO
from validators.results_checks import build_evaluation

OPTIONS = dict(seed=3, months=12, food=4.6, area=50)
EVIDENCE = "data/parameters/evidence_columns_DRAFT.csv"
PARAMETERS = "data/parameters/iberian_lynx_baseline.csv"
SOURCES = "data/parameters/sources.csv"


def developer_that(change):
    def developer(config, round_number, issues, root):
        results = simulator_developer(config, round_number, issues, root)
        change(results)
        return results
    return developer


def evaluator_that(*, status=None, issues=None, fail_first_check=False, extra=None):
    def evaluator(config, results, root, round_number):
        evaluation = build_evaluation(config, results, root, round_number)
        if fail_first_check:
            evaluation["checks"][0]["passed"] = False
        if status is not None:
            evaluation["status"] = status
        if issues is not None:
            evaluation["issues"] = issues
        if extra:
            evaluation.update(extra)
        return evaluation
    return evaluator


def flip_persisted(results):
    results["persisted"] = not results["persisted"]


def source_copy(tmp_path, edit):
    root = tmp_path / "source"
    shutil.copytree(REPO / "data", root / "data")
    edit(root)
    return root


def edit_text(relative, old, new):
    def edit(root):
        path = root / relative
        text = path.read_text(encoding="utf-8")
        assert old in text
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return edit


ONE_ISSUE = [dict(code="x", message="m", requested_change="c")]


@pytest.mark.parametrize("name,keywords", [
    ("flawed results, evaluator forces pass", dict(developer=developer_that(flip_persisted), evaluator=evaluator_that(status="pass"))),
    ("a check marked failed, status pass", dict(evaluator=evaluator_that(fail_first_check=True))),
    ("status pass with issues present", dict(evaluator=evaluator_that(issues=ONE_ISSUE))),
    ("status revise with no issues", dict(evaluator=evaluator_that(status="revise", issues=[]))),
    ("an extra field in the evaluation", dict(evaluator=evaluator_that(extra=dict(note="hi")))),
])
def test_an_evaluation_that_contradicts_itself_or_the_schema_fails_the_case(tmp_path, name, keywords):
    result = run_case(tmp_path / "case", options=OPTIONS, **keywords)
    assert result.status == "failed" and "evaluator failed with ValidationError" in result.reason, name


@pytest.mark.parametrize("change", [
    lambda r: r.update(persisted=float("nan")),
    lambda r: r.update(persisted="yes"),
    lambda r: r.pop("history"),
])
def test_malformed_developer_results_are_rejected_before_the_evaluator_sees_them(tmp_path, change):
    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer_that(change))
    assert result.status == "rejected" and "invalid Developer results" in result.reason


def test_a_reordered_history_is_caught_by_the_code_check_and_stops_the_case(tmp_path):
    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer_that(lambda r: r["history"].reverse()))
    assert result.status == "stop" and result.issues


def test_a_developer_that_edits_the_research_snapshot_is_caught(tmp_path):
    def developer(config, round_number, issues, root):
        path = Path(root) / PARAMETERS
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        path.write_text(path.read_text() + "\n")
        return simulator_developer(config, round_number, issues, root)

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer)
    assert result.status == "failed" and "changed since" in result.reason


@pytest.mark.parametrize("relative,old,new,where", [
    (EVIDENCE, ",medium,", ",ultra,", "evidence gate"),
    (PARAMETERS, "breeding_age_min,3,", "breeding_age_min,nan,", "research files failed validation"),
])
def test_malformed_research_files_are_refused_before_any_role_runs(tmp_path, relative, old, new, where):
    source = source_copy(tmp_path, edit_text(relative, old, new))
    result = run_case(tmp_path / "case", options=OPTIONS, source_root=source)
    assert result.status == "rejected" and where in result.reason


def test_known_gap_results_labelled_sample_pass_the_whole_chain(tmp_path):
    # Found by the red team of 2026-10-29.  A real case should not pass on results labelled "sample"; the fix is to refuse
    # them in run_case.  When it lands, change this test to expect "rejected".
    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer_that(lambda r: r.update(data_kind="sample")))
    assert result.status == "pass"


def test_known_gap_a_spreadsheet_formula_in_a_source_cell_is_accepted(tmp_path):
    # Found by the red team of 2026-10-29.  Python ignores the formula, but a spreadsheet that opens sources.csv would run it.
    # The fix is for the validator to refuse text cells that start with =, +, or @.  When it lands, expect "rejected".
    source = source_copy(tmp_path, edit_text(SOURCES, "full text", '=HYPERLINK("http://example.invalid")'))
    result = run_case(tmp_path / "case", options=OPTIONS, source_root=source)
    assert result.status == "pass"
