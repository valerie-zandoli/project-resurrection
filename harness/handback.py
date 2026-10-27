"""The hand-back path:  one batched Researcher round per case, then escalate or fail.

This code is the guarantee behind `docs/handoff-decisions.md` (clarification round, failure
behavior, transient retries).  It holds the rules and the counts; it sends no message, calls
no model, and does not judge the science.  A person decides every escalated case.
"""

from dataclasses import dataclass, field

CLASSIFICATIONS = ("required", "optional")
FILED_BY = ("developer", "evaluator")
OUTCOMES = ("resolved_with_evidence", "resolved_with_approved_assumption", "unresolved")
OWNERS = ("Valerie", "Anastasiya")
MAX_RETRIES_PER_CALL = 1
MAX_RETRIES_PER_ROUND = 3
MAX_RETRIES_PER_CASE = 10  # all three bounds are guesses until real runs measure them

# Faults that more evidence cannot fix:  never retried, reported with the specific reason.
FAIL_EXPLICITLY = ("schema_mismatch", "stale_input", "killed_run", "model_output_failed_check",
                   "unresolved_issue_at_round_3")


class HandbackError(Exception):
    """A rule of the hand-back path was broken."""


class BudgetExhausted(HandbackError):
    """The case already used its one Researcher round."""


def _text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise HandbackError(f"{name} must be a nonempty string")
    return value.strip()


@dataclass(frozen=True)
class Request:
    """One gap.  The reason for the classification is required so a reviewer can see why."""
    case_id: str
    run_id: str
    parameter: str
    missing: str
    classification: str
    classification_reason: str
    filed_by: str
    resolution_needed: str

    def __post_init__(self):
        for name in ("case_id", "run_id", "parameter", "missing", "classification_reason", "resolution_needed"):
            _text(name, getattr(self, name))
        if self.classification not in CLASSIFICATIONS:
            raise HandbackError(f"classification must be one of {CLASSIFICATIONS}")
        if self.filed_by not in FILED_BY:
            raise HandbackError(f"filed_by must be one of {FILED_BY}")


@dataclass(frozen=True)
class Response:
    """The Researcher's answer to one request.  An assumption needs a named human reviewer."""
    parameter: str
    outcome: str
    answer: str
    reviewer: str
    reason: str

    def __post_init__(self):
        _text("parameter", self.parameter)
        if self.outcome not in OUTCOMES:
            raise HandbackError(f"outcome must be one of {OUTCOMES}")
        _text("reason", self.reason)
        if self.outcome != "unresolved":
            _text("answer", self.answer)
            _text("reviewer", self.reviewer)


def classify_fault(fault):
    """Return "retry" for a transient provider or network error and "fail" for everything else.

    `fault` is an exception, an HTTP status code, or one of FAIL_EXPLICITLY.  Transient:  a
    timeout, a connection reset, HTTP 429, and HTTP 5xx.  Any other 4xx, a schema or validation
    failure, a failed model-output check, and a killed run are not retried.
    """
    if isinstance(fault, (TimeoutError, ConnectionResetError)):
        return "retry"
    if isinstance(fault, bool):
        return "fail"
    if isinstance(fault, int):
        return "retry" if fault == 429 or 500 <= fault <= 599 else "fail"
    return "fail"


@dataclass
class Case:
    """One run chain, from the first input until pass or stop.  The budgets belong to the case."""
    case_id: str
    run_ids: list = field(default_factory=list)
    round_used: bool = False
    requests: list = field(default_factory=list)
    responses: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    retry_log: list = field(default_factory=list)
    failures: list = field(default_factory=list)
    stopped: bool = False
    stop_reason: str = ""

    def start_run(self, run_id):
        """A deliberate research change starts a new run inside the same case; the budgets carry over."""
        self.run_ids.append(_text("run_id", run_id))

    def _require_active(self):
        if self.stopped:
            raise HandbackError(f"case {self.case_id} is stopped:  {self.stop_reason}")
        if not self.run_ids:
            raise HandbackError("start a run before filing requests")

    def _stop(self, reason):
        self.stopped = True
        self.stop_reason = reason
        return self.report()

    def open_round(self, requests):
        """File every open gap in one batch.  A second call raises, whoever files it."""
        self._require_active()
        if self.round_used:
            raise BudgetExhausted(f"case {self.case_id} already used its one Researcher round")
        if not requests:
            raise HandbackError("a round needs at least one request")
        parameters = [r.parameter for r in requests]
        if any(r.case_id != self.case_id for r in requests):
            raise HandbackError("a request names another case")
        if len(set(parameters)) != len(parameters):
            raise HandbackError("batch every open parameter once:  a parameter appears twice")
        self.round_used = True
        self.requests = list(requests)
        return self.requests

    def close_round(self, responses):
        """Match responses to requests.  A required gap left unresolved stops the case."""
        self._require_active()
        if not self.round_used or self.responses:
            raise HandbackError("there is no open round to close")
        known = {r.parameter for r in self.requests}
        by_parameter = {}
        for response in responses:
            if response.parameter not in known:
                raise HandbackError(f"response for {response.parameter!r} answers no request")
            if response.parameter in by_parameter:
                raise HandbackError(f"two responses for {response.parameter!r}")
            by_parameter[response.parameter] = response
        self.responses = list(by_parameter.values())
        unresolved = []
        for request in self.requests:
            response = by_parameter.get(request.parameter)
            if response is None or response.outcome == "unresolved":
                reason = response.reason if response else "no response"
                if request.classification == "required":
                    unresolved.append(f"{request.parameter}: {reason}")
                else:
                    self.limitations.append(f"{request.parameter}: {reason}")
        if unresolved:
            return self._stop("required gap unresolved after the one round:  " + "; ".join(unresolved))
        return self.report()

    def new_gap(self, request):
        """A gap found after the round.  Never a second round:  required stops, optional is logged."""
        self._require_active()
        if not self.round_used:
            raise HandbackError("no round was used yet:  file the gap in the round")
        if request.classification == "required":
            return self._stop(f"new required gap after the one round:  {request.parameter}: {request.missing}")
        self.limitations.append(f"{request.parameter}: {request.missing}")
        return self.report()

    def retry(self, call_id, round_number, fault):
        """Count one transient retry.  True means retry; a fault that is never retried is recorded as a
        failure of that call (the caller rejects the attempt); a bound reached stops the case."""
        self._require_active()
        if classify_fault(fault) != "retry":
            self.failures.append(dict(call_id=call_id, round=round_number, error=repr(fault)))
            return False
        per_call = sum(e["call_id"] == call_id and e["round"] == round_number for e in self.retry_log)
        per_round = sum(e["round"] == round_number for e in self.retry_log)
        if (per_call >= MAX_RETRIES_PER_CALL or per_round >= MAX_RETRIES_PER_ROUND
                or len(self.retry_log) >= MAX_RETRIES_PER_CASE):
            self._stop(f"retry bound reached at {call_id} (round {round_number}):  {fault!r}")
            return False
        self.retry_log.append(dict(call_id=call_id, round=round_number, error=repr(fault)))
        return True

    def report(self):
        """What a person needs to decide an escalated case.  Nothing is dropped or reset."""
        return dict(
            case_id=self.case_id, run_ids=list(self.run_ids), status="stopped" if self.stopped else "open",
            stop_reason=self.stop_reason, notify=list(OWNERS), round_used=self.round_used,
            requests=[vars(r) for r in self.requests], responses=[vars(r) for r in self.responses],
            limitations=list(self.limitations), retries=list(self.retry_log),
            failures=list(self.failures))
