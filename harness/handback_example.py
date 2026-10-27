"""One scripted hand-back example:  a batched request, the single Researcher round, and the stop.

This runs the rules of `harness/handback.py` on two real gaps in the research files, with scripted
answers in place of a model, and writes `case.json` and `trace.jsonl` in the shape that the fallback
bundle expects in `hand-back/` (`scripts/check_fallback.py`):

    python -m harness.handback_example --output hand-back

It calls no model and needs no key.  What it shows is the code path, not a Researcher's judgment:
the required gap is left open, so the case stops and names both owners; the optional gap becomes a
logged limitation; a second round is refused.
"""

import argparse
import json
import sys
from pathlib import Path

from harness.handback import BudgetExhausted, Case, HandbackError, Request, Response
from harness.trace import Trace

CAPTION = "scripted hand-back example; no model is called"
CASE_ID = "handback-example-1"
RUN_ID = "handback-example-1-run-1"

# Two real gaps.  The model uses the female home range to count territories, so a gap there is
# required; it does not use the diet share, so a gap there is optional.
REQUESTS = (
    dict(parameter="female_home_range_km2",
         missing="A measured female home range for Andujar-Cardena.  The 10 km2 average comes from a "
                 "web summary that names no study, and the evidence file labels it low.",
         classification="required",
         classification_reason="The home range sets the number of female territories (area divided by "
                               "home range), so the persistence endpoint depends on it.",
         resolution_needed="A primary study, read in full, that measures female home range in "
                           "Andujar-Cardena, with its sample size."),
    dict(parameter="diet_rabbit_fraction",
         missing="A primary study for the rabbit share of the diet; the two sources name none.",
         classification="optional",
         classification_reason="The simulator does not use the diet share, so the run does not depend on it.",
         resolution_needed="A primary diet study read in full, or the share labeled as an assumption."),
)

# The scripted Researcher's answers:  neither gap can be closed from the source registry.
RESPONSES = (
    dict(parameter="female_home_range_km2", outcome="unresolved", answer="", reviewer="",
         reason="No source in the registry measures female home range in Andujar-Cardena; the measured "
                "ranges are from Donana."),
    dict(parameter="diet_rabbit_fraction", outcome="unresolved", answer="", reviewer="",
         reason="No primary diet study is in the registry."),
)


def run_example(output):
    """Write the example into the new folder `output` and return the hand-back report."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"output folder already exists; use a new one: {output}")
    output.mkdir(parents=True)
    trace = Trace(output / "trace.jsonl")
    trace.add("harness", f"{CAPTION}:  case {CASE_ID} started")
    case = Case(CASE_ID)
    case.start_run(RUN_ID)

    requests = [Request(case_id=CASE_ID, run_id=RUN_ID, filed_by="evaluator", **fields) for fields in REQUESTS]
    case.open_round(requests)
    trace.add("evaluator", "filed one batched request for the single Researcher round",
              tool_args=[dict(parameter=r.parameter, classification=r.classification) for r in requests])

    responses = [Response(**fields) for fields in RESPONSES]
    trace.add("researcher", "answered every request in the round (scripted)",
              tool_result=[dict(parameter=r.parameter, outcome=r.outcome) for r in responses])
    report = case.close_round(responses)
    trace.add("harness", f"round closed:  case {report['status']}", validator=report["stop_reason"] or "ok")

    try:
        case.open_round([Request(case_id=CASE_ID, run_id=RUN_ID, filed_by="developer", **REQUESTS[0])])
        second_round = "opened (this must not happen)"
    except (BudgetExhausted, HandbackError) as exc:
        second_round = f"refused:  {exc}"
    trace.add("harness", f"a second round was {second_round}")

    summary = dict(case_id=CASE_ID, status="stop" if report["status"] == "stopped" else "pass",
                   reason=report["stop_reason"] or "every gap resolved", mode="scripted_handback_example",
                   caption=CAPTION, notify=report["notify"], second_round=second_round, handback=report)
    (output / "case.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    trace.add("harness", f"{CAPTION}:  case.json written")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="new folder; never overwritten")
    args = parser.parse_args(argv)
    try:
        report = run_example(args.output)
    except OSError as exc:
        print(f"Hand-back example failed to start: {exc}", file=sys.stderr)
        return 2
    print(f"Caption: {CAPTION}")
    print(f"Case {report['status']}:  {report['stop_reason'] or 'every gap resolved'}")
    print(f"Limitations logged:  {'; '.join(report['limitations']) or 'none'}")
    print(f"Saved to {args.output} (case.json, trace.jsonl).")
    print(f"Caption: {CAPTION}")
    return 0 if report["status"] != "stopped" else 1


if __name__ == "__main__":
    raise SystemExit(main())
