"""Check that the fallback bundle for the demonstration is complete, so that no step depends on the key.

Run it from the repository root before 2026-11-01 (`docs/demo-plan.md`, "The fallback"):

    python scripts/check_fallback.py --root fallback

The bundle is a folder with this layout (a proposal; change `LAYOUT` and the docs together):

    history/report.json                  the history test report, from the one pre-registered run
    batches/pilot/batch.json             the pilot grid (100 trials per cell)
    batches/final/batch.json             the final grid (500 trials per cell)
    batches/final/table1.md              the table and the figure of the final grid
    batches/final/figure1.svg
    case/input.json, results.json,       one saved case:  its input, results, and evaluation, the harness's
    evaluation.json, case.json,          case summary, and the trace of the live pass
    trace.jsonl
    hand-back/case.json, trace.jsonl     the hand-back example
    deck/<name>.pdf                      the slide PDF

Each item is OK, MISSING, or BAD, with the reason.  The script only reads:  it changes nothing, calls no model,
needs no key, and never runs the history test.  A trace that holds key-like text is BAD.

Exit code:  0 = every item is OK;  1 = at least one item is MISSING or BAD;  2 = the root is not a folder.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validators.handoff_hashes import check_handoff_hashes  # noqa: E402

RUN_SEED = 20261101  # the run seed of docs/history-preregistration.md
PILOT_TRIALS, FINAL_TRIALS = 100, 500
CELLS = 6  # three food levels by two areas
KEY_LIKE = re.compile(r"sk-[A-Za-z0-9_-]{16,}|ANTHROPIC_API_KEY")
CASE_STATUSES = {"pass", "stop", "rejected", "failed"}
EVALUATION_STATUSES = {"pass", "revise", "stop"}

LAYOUT = {
    "history": "history/report.json",
    "pilot": "batches/pilot/batch.json",
    "final": "batches/final/batch.json",
    "table": "batches/final/table1.md",
    "figure": "batches/final/figure1.svg",
    "input": "case/input.json",
    "results": "case/results.json",
    "evaluation": "case/evaluation.json",
    "case": "case/case.json",
    "trace": "case/trace.jsonl",
    "handback_case": "hand-back/case.json",
    "handback_trace": "hand-back/trace.jsonl",
}
DECK = "deck"


class Bad(Exception):
    """An item exists but is not usable."""


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise Bad(f"cannot read the file ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise Bad(f"not valid JSON ({exc.msg} at line {exc.lineno})") from exc


def check_history(path, run_seed=RUN_SEED):
    report = read_json(path)
    if report.get("run_seed") != run_seed:
        raise Bad(f"run_seed is {report.get('run_seed')!r}; the pre-registration names {run_seed}")
    if report.get("verdict", {}).get("result") not in ("pass", "fail"):
        raise Bad("the verdict is missing or is neither pass nor fail")
    areas = report.get("areas")
    if not areas or not areas[0].get("main_run"):
        raise Bad("the first area is not the main run")
    if len(report.get("must_say", [])) < 7:
        raise Bad("the statements that the report must say are missing")
    if len(str(report.get("parameters_sha256", ""))) != 64:
        raise Bad("the hash of the parameter file is missing")


def check_batch(path, trials):
    batch = read_json(path)
    if not str(batch.get("format_version", "")).startswith("preview-batch"):
        raise Bad("not a batch file (format_version)")
    if batch.get("status") != "completed":
        raise Bad(f"the batch status is {batch.get('status')!r}, not completed")
    cells = batch.get("cells", [])
    if len(cells) != CELLS:
        raise Bad(f"{len(cells)} cells; the grid has {CELLS}")
    for cell in cells:
        name = cell.get("name", "?")
        if cell.get("status") != "completed":
            raise Bad(f"cell {name} is {cell.get('status')!r}, not completed")
        if cell.get("planned_trials") != trials or len(cell.get("trials", [])) != trials:
            raise Bad(f"cell {name} has {len(cell.get('trials', []))} trials and plans {cell.get('planned_trials')}; "
                      f"expected {trials}")
        if any(trial.get("status") != "completed" for trial in cell["trials"]):
            raise Bad(f"cell {name} has a trial that did not complete")


def check_text_file(path, marker=None):
    text = path.read_text(encoding="utf-8", errors="replace")
    if marker and marker not in text:
        raise Bad(f"does not look like the expected file (no {marker!r})")


def check_trace(path):
    lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    if len(lines) < 3:
        raise Bad(f"{len(lines)} lines; a trace has one line for every step")
    for number, line in enumerate(lines, 1):
        if KEY_LIKE.search(line):
            raise Bad(f"line {number} holds key-like text")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Bad(f"line {number} is not valid JSON ({exc.msg})") from exc
        if row.get("step") != number or "role" not in row:
            raise Bad(f"line {number} is not step {number} with a role")


def check_case_summary(path):
    case = read_json(path)
    if case.get("status") not in CASE_STATUSES:
        raise Bad(f"status {case.get('status')!r} is not one of {sorted(CASE_STATUSES)}")


def check_case_files(root):
    """The saved case:  the same run in input, results, and evaluation, and the same research-file hashes."""
    run_input = read_json(root / LAYOUT["input"])
    results = read_json(root / LAYOUT["results"])
    evaluation = read_json(root / LAYOUT["evaluation"])
    ids = {run_input.get("run_id"), results.get("run_id"), evaluation.get("run_id")}
    if len(ids) != 1 or None in ids:
        raise Bad(f"the run IDs differ or are missing: {sorted(map(str, ids))}")
    if evaluation.get("status") not in EVALUATION_STATUSES:
        raise Bad(f"the evaluation status {evaluation.get('status')!r} is not pass, revise, or stop")
    try:
        errors = check_handoff_hashes(run_input, results, evaluation)
    except (KeyError, TypeError) as exc:
        raise Bad(f"a hash field is missing ({exc})") from exc
    if errors:
        raise Bad("; ".join(errors))


def check_deck(folder):
    pdfs = sorted(folder.glob("*.pdf")) if folder.is_dir() else []
    if not pdfs:
        return None
    for pdf in pdfs:
        data = pdf.read_bytes()
        if data[:5] == b"%PDF-" and len(data) > 1000:
            return pdf.name
    raise Bad("no PDF in the folder starts with %PDF- and has content")


def run_checks(root, *, run_seed=RUN_SEED, pilot_trials=PILOT_TRIALS, final_trials=FINAL_TRIALS):
    """Return a list of (item, status, detail); status is OK, MISSING, or BAD.  Nothing is written."""
    root = Path(root)
    checks = {
        "history": lambda p: check_history(p, run_seed),
        "pilot": lambda p: check_batch(p, pilot_trials),
        "final": lambda p: check_batch(p, final_trials),
        "table": lambda p: check_text_file(p, "|"),
        "figure": lambda p: check_text_file(p, "<svg"),
        "input": lambda p: read_json(p),
        "results": lambda p: read_json(p),
        "evaluation": lambda p: read_json(p),
        "case": check_case_summary,
        "trace": check_trace,
        "handback_case": check_case_summary,
        "handback_trace": check_trace,
    }
    rows = []
    for key, relative in LAYOUT.items():
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            rows.append((relative, "MISSING", "the file is not there or is empty"))
            continue
        try:
            checks[key](path)
            rows.append((relative, "OK", ""))
        except Bad as exc:
            rows.append((relative, "BAD", str(exc)))
    if all(root.joinpath(LAYOUT[k]).is_file() for k in ("input", "results", "evaluation")):
        try:
            check_case_files(root)
            rows.append(("case/ (input, results, evaluation agree)", "OK", ""))
        except Bad as exc:
            rows.append(("case/ (input, results, evaluation agree)", "BAD", str(exc)))
    else:
        rows.append(("case/ (input, results, evaluation agree)", "MISSING", "one of the three files is missing"))
    try:
        name = check_deck(root / DECK)
        rows.append((f"{DECK}/*.pdf", "OK" if name else "MISSING", name or "no PDF in the folder"))
    except Bad as exc:
        rows.append((f"{DECK}/*.pdf", "BAD", str(exc)))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path("fallback"), help="the bundle folder (default: fallback)")
    parser.add_argument("--run-seed", type=int, default=RUN_SEED, help="the pre-registered run seed")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        print(f"{args.root} is not a folder.", file=sys.stderr)
        return 2
    rows = run_checks(args.root, run_seed=args.run_seed)
    for item, status, detail in rows:
        print(f"{status:<8}{item}" + (f":  {detail}" if detail else ""))
    ready = sum(status == "OK" for _, status, _ in rows)
    print(f"{ready} of {len(rows)} items are ready.  Nothing was changed.")
    return 0 if ready == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
