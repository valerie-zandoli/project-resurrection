"""The offline harness skeleton:  one case, from the research files to pass, stop, or reject.

No model is called here.  The Developer is the fixed `run_model` tool (the simulator) and the
Evaluator is the code checks, so every rule that the harness guarantees can be tested without a
key.  Roles that call a model replace these two functions later; the loop does not change.

The harness, not an agent, does all of the following (docs/architecture.md, "Enforced by"):
validates the research files, makes the read-only snapshot, computes the hashes, compares them
at every handoff, counts the revision rounds (at most 3), and writes the trace.
"""

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

from harness.handback import OWNERS, Case
from harness.snapshot import RESEARCH_FILES, make_snapshot
from harness.trace import Trace, scrub
from simulation.model import REPO, preview_config, simulate
from validators.handoff_hashes import check_files_current, check_handoff_hashes
from validators.parameters import validate_parameters
from validators.results_checks import build_evaluation

MAX_ROUNDS = 3
EVALUATION_SCHEMA = json.loads((REPO / "schemas" / "evaluation.schema.json").read_text(encoding="utf-8"))


class HarnessError(Exception):
    """The harness could not start (for example, the output folder exists)."""


@dataclass
class CaseResult:
    status: str  # pass, stop, rejected, or failed
    reason: str
    attempts: int
    issues: list = field(default_factory=list)
    run_dir: Path = None


def simulator_developer(config, round_number, issues, root):
    """The Developer of the skeleton:  the fixed run_model tool.  It writes no code."""
    results = simulate(config, root=root)
    results["revision_round"] = round_number
    return results


def code_evaluator(config, results, root, round_number):
    """The Evaluator of the skeleton:  the code checks (`check_artifacts`)."""
    return build_evaluation(config, results, root, round_number)


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run_case(output, *, options, source_root=REPO, developer=simulator_developer,
             evaluator=code_evaluator, max_rounds=MAX_ROUNDS):
    """Run one case into a new folder.  `options` holds seed, months, food, and area."""
    output = Path(output)
    if output.exists():
        raise HarnessError(f"output folder already exists; use a new one: {output}")
    output.mkdir(parents=True)
    trace = Trace(output / "trace.jsonl")
    case = Case(output.name)
    state = dict(hashes={}, issues=[], attempts=0)

    def finish(status, reason, issues=None):
        issues = issues if issues is not None else state["issues"]
        trace.add("harness", f"case finished: {status}", validator=reason if status != "pass" else None)
        summary = dict(case_id=case.case_id, status=status, reason=reason, attempts=state["attempts"],
                       run_ids=list(case.run_ids), issues=issues, research_sha256=state["hashes"],
                       notify=[] if status == "pass" else list(OWNERS), clarification=case.report())
        _write(output / "case.json", summary)
        return CaseResult(status, reason, state["attempts"], issues, output)

    # 1. Snapshot and hash.  The agents carry these hashes unchanged.
    snapshot_root = output / "snapshot"
    try:
        state["hashes"] = make_snapshot(source_root, snapshot_root)
    except OSError as exc:
        trace.add("harness", "research files could not be copied", validator=str(exc))
        shutil.rmtree(snapshot_root, ignore_errors=True)  # no half-made snapshot is left to read
        return finish("rejected", f"research files could not be read: {exc}", [])
    trace.input_hashes = state["hashes"]
    trace.add("harness", "read-only snapshot of the research files made", validator="ok")

    # 2. Validate the SNAPSHOT, as CODE, so that the validated bytes are the bytes that the agents read.
    #    A failure stops the case before anything runs.
    paths = [snapshot_root / relative for relative in RESEARCH_FILES]
    errors = validate_parameters(*paths)
    if errors:
        trace.add("harness", "research files failed validation", validator=errors)
        shutil.rmtree(snapshot_root, ignore_errors=True)  # nothing that failed validation is left for an agent to read
        return finish("rejected", "research files failed validation: " + "; ".join(errors[:3]), [])
    trace.add("harness", "research files passed validation", validator="ok")

    config = preview_config(options["seed"], options["months"], options["food"], options["area"],
                            root=snapshot_root)
    case.start_run(config["run_id"])
    trace.add("harness", f"input written for run {config['run_id']}", tool_args=options)

    issues = []
    for round_number in range(max_rounds + 1):
        round_dir = output / f"round_{round_number}"
        errors = check_files_current(config, snapshot_root)
        if errors:
            trace.add("harness", "research files changed since the snapshot", validator=errors,
                      revision_round=round_number)
            return finish("rejected", "research files changed since the input was written (no retry): "
                          + "; ".join(errors))
        _write(round_dir / "input.json", config)
        state["attempts"] += 1

        try:
            results = developer(config, round_number, issues, snapshot_root)
        except Exception as exc:  # a failure of the Developer is reported, never retried
            reason, _ = scrub(f"developer failed with {type(exc).__name__}: {exc}")
            trace.add("developer", reason, tool="run_model", revision_round=round_number)
            return finish("failed", reason + " (no retry)")
        _write(round_dir / "results.json", results)
        trace.add("developer", "results returned", tool="run_model", tool_args=options,
                  tool_result=f"persisted={results.get('persisted')}", revision_round=round_number)
        errors = check_handoff_hashes(config, results)
        if errors:
            trace.add("harness", "hashes differ between input and results", validator=errors,
                      revision_round=round_number)
            return finish("rejected", "hash mismatch between input and results (no retry): " + "; ".join(errors))

        try:
            evaluation = evaluator(config, results, snapshot_root, round_number)
            # Only a schema-valid evaluation is a record; a refusal, a guess, or nothing fails the case.
            jsonschema.validate(evaluation, EVALUATION_SCHEMA)
        except Exception as exc:
            reason, _ = scrub(f"evaluator failed with {type(exc).__name__}: {exc}")
            trace.add("evaluator", reason, tool="check_artifacts", revision_round=round_number)
            return finish("failed", reason + " (no retry)")
        _write(round_dir / "evaluation.json", evaluation)
        issues = evaluation["issues"]
        state["issues"] = issues
        trace.add("evaluator", f"{len(issues)} issue(s)", tool="check_artifacts",
                  tool_result=[issue["code"] for issue in issues], evaluator_status=evaluation["status"],
                  revision_round=round_number)
        errors = check_handoff_hashes(config, results, evaluation)
        if errors:
            trace.add("harness", "hashes differ between input, results, and evaluation", validator=errors,
                      revision_round=round_number)
            return finish("rejected", "hash mismatch in the evaluation (no retry): " + "; ".join(errors))

        if evaluation["status"] == "pass":
            return finish("pass", "every check passed", [])
        if evaluation["status"] == "stop" or round_number == max_rounds:
            return finish("stop", f"unresolved issues at revision round {round_number}")
        # status is "revise":  the issues go back to the Developer in the next round.
    return finish("stop", "round limit reached")  # unreachable, kept as a guard
