"""The hand-back path:  one batched round, escalate on a required gap, fail without retry."""

import pytest

from harness.handback import (BudgetExhausted, Case, HandbackError, Request, Response,
                              classify_fault)


def request(parameter="annual_mortality_rate_all_causes", classification="required", filed_by="evaluator",
            case_id="case-1"):
    return Request(case_id=case_id, run_id="run-1", parameter=parameter,
                   missing="The unit is not stated.", classification=classification,
                   classification_reason="The run cannot be interpreted without the unit.",
                   filed_by=filed_by, resolution_needed="Name the unit and the passage that gives it.")


def answer(parameter="annual_mortality_rate_all_causes", outcome="resolved_with_evidence"):
    return Response(parameter=parameter, outcome=outcome, answer="Page 4, Table 2.", reviewer="Valerie",
                    reason="The unit is stated in the source.")


@pytest.fixture
def case():
    case = Case("case-1")
    case.start_run("run-1")
    return case


@pytest.mark.parametrize("field, value", [
    ("case_id", ""), ("run_id", " "), ("parameter", ""), ("missing", ""), ("classification", "maybe"),
    ("classification_reason", ""), ("filed_by", "harness"), ("resolution_needed", ""),
])
def test_a_request_needs_every_field(field, value):
    fields = dict(case_id="c", run_id="r", parameter="p", missing="m", classification="required",
                  classification_reason="why", filed_by="developer", resolution_needed="n")
    fields[field] = value
    with pytest.raises(HandbackError):
        Request(**fields)


def test_a_resolved_response_needs_an_answer_and_a_named_reviewer():
    with pytest.raises(HandbackError):
        Response("p", "resolved_with_evidence", "", "Valerie", "why")
    with pytest.raises(HandbackError):
        Response("p", "resolved_with_approved_assumption", "an assumption", "", "why")
    with pytest.raises(HandbackError):
        Response("p", "resolved_by_magic", "a", "Valerie", "why")
    assert Response("p", "unresolved", "", "", "no evidence found").outcome == "unresolved"


def test_one_round_per_case_whoever_files_it(case):
    case.open_round([request("a", filed_by="developer"), request("b", filed_by="evaluator")])
    with pytest.raises(BudgetExhausted):
        case.open_round([request("c")])


def test_the_round_batches_every_open_parameter_once(case):
    with pytest.raises(HandbackError, match="twice"):
        case.open_round([request("a"), request("a")])
    assert not case.round_used
    with pytest.raises(HandbackError, match="at least one"):
        case.open_round([])
    with pytest.raises(HandbackError, match="another case"):
        case.open_round([request("a", case_id="case-2")])


def test_a_round_needs_a_run_first():
    with pytest.raises(HandbackError, match="start a run"):
        Case("c").open_round([request(case_id="c")])


def test_all_gaps_resolved_keeps_the_case_open(case):
    case.open_round([request("a"), request("b", classification="optional")])
    report = case.close_round([answer("a"), answer("b", "resolved_with_approved_assumption")])
    assert report["status"] == "open" and not case.stopped and report["limitations"] == []


def test_a_required_gap_left_unresolved_stops_the_case_and_reports_to_both_owners(case):
    case.open_round([request("a"), request("b")])
    report = case.close_round([answer("a"), Response("b", "unresolved", "", "", "no source gives it")])
    assert report["status"] == "stopped" and "b: no source gives it" in report["stop_reason"]
    assert report["notify"] == ["Valerie", "Anastasiya"]
    assert [r["parameter"] for r in report["requests"]] == ["a", "b"]
    assert len(report["responses"]) == 2
    with pytest.raises(HandbackError, match="stopped"):
        case.open_round([request("c")])


def test_a_missing_response_to_a_required_request_counts_as_unresolved(case):
    case.open_round([request("a"), request("b")])
    report = case.close_round([answer("a")])
    assert report["status"] == "stopped" and "b: no response" in report["stop_reason"]


def test_an_optional_gap_never_stops_the_case(case):
    case.open_round([request("a", classification="optional"), request("b")])
    report = case.close_round([Response("a", "unresolved", "", "", "no data"), answer("b")])
    assert report["status"] == "open"
    assert report["limitations"] == ["a: no data"]


def test_a_response_must_answer_a_request_once(case):
    case.open_round([request("a")])
    with pytest.raises(HandbackError, match="answers no request"):
        case.close_round([answer("zzz")])
    with pytest.raises(HandbackError, match="two responses"):
        case.close_round([answer("a"), answer("a")])
    fresh = Case("c")
    fresh.start_run("r")
    with pytest.raises(HandbackError, match="no open round"):
        fresh.close_round([])


def test_a_new_required_gap_after_the_round_stops_and_never_opens_a_second_round(case):
    case.open_round([request("a")])
    case.close_round([answer("a")])
    report = case.new_gap(request("late", filed_by="developer"))
    assert report["status"] == "stopped" and "late" in report["stop_reason"]
    with pytest.raises(HandbackError):
        case.open_round([request("again")])


def test_a_new_optional_gap_after_the_round_is_a_logged_limitation(case):
    case.open_round([request("a")])
    case.close_round([answer("a")])
    report = case.new_gap(request("late", classification="optional"))
    assert report["status"] == "open" and report["limitations"] == ["late: The unit is not stated."]


def test_a_new_gap_before_any_round_belongs_in_the_round(case):
    with pytest.raises(HandbackError, match="file the gap in the round"):
        case.new_gap(request("a"))


def test_a_deliberate_research_change_starts_a_new_run_but_keeps_the_spent_budget(case):
    case.open_round([request("a")])
    case.close_round([answer("a")])
    case.start_run("run-2")
    assert case.run_ids == ["run-1", "run-2"]
    with pytest.raises(BudgetExhausted):
        case.open_round([request("b")])


@pytest.mark.parametrize("fault, expected", [
    (TimeoutError(), "retry"), (ConnectionResetError(), "retry"), (429, "retry"), (500, "retry"),
    (503, "retry"), (599, "retry"), (400, "fail"), (401, "fail"), (404, "fail"), (200, "fail"),
    (600, "fail"), ("schema_mismatch", "fail"), ("stale_input", "fail"), ("killed_run", "fail"),
    ("model_output_failed_check", "fail"), (ValueError("bad"), "fail"), (True, "fail"),
])
def test_only_transient_provider_and_network_faults_are_retried(fault, expected):
    assert classify_fault(fault) == expected


def test_a_fault_that_is_never_retried_is_recorded_and_not_counted(case):
    assert case.retry("call-1", 0, "schema_mismatch") is False
    assert case.retry_log == [] and case.failures[0]["call_id"] == "call-1"
    assert not case.stopped


def test_one_retry_per_call(case):
    assert case.retry("call-1", 0, 503) is True
    assert case.retry("call-1", 0, 503) is False
    assert case.stopped and "call-1" in case.stop_reason


def test_three_retries_per_round_then_the_case_stops(case):
    assert [case.retry(f"call-{i}", 0, 429) for i in range(3)] == [True, True, True]
    assert case.retry("call-3", 0, 429) is False
    assert case.stopped and "round 0" in case.stop_reason


def test_ten_retries_per_case_across_rounds(case):
    results = [case.retry(f"call-{i}", i // 3, TimeoutError()) for i in range(10)]
    assert all(results) and not case.stopped
    assert case.retry("call-10", 3, TimeoutError()) is False and case.stopped


def test_each_retry_is_logged_with_its_error_apart_from_revisions(case):
    case.retry("call-1", 2, 503)
    assert case.retry_log == [dict(call_id="call-1", round=2, error="503")]
    assert case.report()["retries"] == case.retry_log


def test_a_stopped_case_refuses_more_retries(case):
    case.retry("c", 0, 503)
    case.retry("c", 0, 503)
    with pytest.raises(HandbackError, match="stopped"):
        case.retry("d", 0, 503)


def test_the_report_keeps_everything_for_the_person_who_decides(case):
    case.open_round([request("a")])
    report = case.close_round([Response("a", "unresolved", "", "", "none")])
    assert {"case_id", "run_ids", "status", "stop_reason", "notify", "requests", "responses",
            "limitations", "retries", "failures"} <= set(report)
    assert report["requests"][0]["classification_reason"] and report["requests"][0]["resolution_needed"]
