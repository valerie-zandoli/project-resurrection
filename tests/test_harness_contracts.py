"""The harness rejects invalid callback handoffs before trusting their verdicts."""

import pytest

from harness.run_case import HarnessError, run_case, simulator_developer
from validators.results_checks import build_evaluation

OPTIONS = dict(seed=3, months=12, food=4.6, area=50)


@pytest.mark.parametrize("limit", [4, -1, True, 1.5, "3"])
def test_a_caller_cannot_override_the_hard_revision_cap(tmp_path, limit):
    with pytest.raises(HarnessError, match="max_rounds"):
        run_case(tmp_path / "case", options=OPTIONS, max_rounds=limit)
    assert not (tmp_path / "case").exists()


@pytest.mark.parametrize("field,value", [("run_id", "another-run"), ("revision_round", 3)])
def test_an_evaluation_for_another_run_or_round_is_rejected(tmp_path, field, value):
    def evaluator(config, results, root, round_number):
        evaluation = build_evaluation(config, results, root, round_number)
        evaluation[field] = value
        return evaluation

    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=evaluator)
    assert result.status == "rejected" and "evaluation identity" in result.reason
    assert result.attempts == 1


@pytest.mark.parametrize("change", ["missing", "duplicate", "arbitrary"])
def test_a_pass_cannot_omit_or_duplicate_required_checks(tmp_path, change):
    def evaluator(config, results, root, round_number):
        evaluation = build_evaluation(config, results, root, round_number)
        if change == "missing":
            evaluation["checks"].pop()
        elif change == "duplicate":
            evaluation["checks"].append(evaluation["checks"][0])
        else:
            evaluation["checks"] = [dict(name="arbitrary", passed=True, detail="ok")]
        return evaluation

    result = run_case(tmp_path / "case", options=OPTIONS, evaluator=evaluator)
    assert result.status == "rejected" and "required check" in result.reason


@pytest.mark.parametrize("field,value", [("run_id", "another-run"), ("seed", 999), ("revision_round", 3)])
def test_results_identity_is_checked_before_calling_the_evaluator(tmp_path, field, value):
    evaluated = []

    def developer(config, round_number, issues, root):
        results = simulator_developer(config, round_number, issues, root)
        results[field] = value
        return results

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer,
                      evaluator=lambda *args: evaluated.append(True))
    assert result.status == "rejected" and "identity" in result.reason
    assert evaluated == []


@pytest.mark.parametrize("bad_results", [None, {}, {"persisted": float("nan")}])
def test_malformed_results_fail_loudly_without_crashing_the_harness(tmp_path, bad_results):
    evaluated = []
    result = run_case(tmp_path / "case", options=OPTIONS, developer=lambda *args: bad_results,
                      evaluator=lambda *args: evaluated.append(True))
    assert result.status == "rejected" and "invalid Developer results" in result.reason
    assert evaluated == []


def test_a_lower_revision_budget_still_works(tmp_path):
    def developer(config, round_number, issues, root):
        results = simulator_developer(config, round_number, issues, root)
        results["persisted"] = not results["persisted"]
        return results

    result = run_case(tmp_path / "case", options=OPTIONS, developer=developer, max_rounds=0)
    assert result.status == "stop" and result.attempts == 1
