"""The evidence gate:  every run checks the research evidence before it starts (docs/failure-taxonomy.md).

The Researcher writes an evidence file beside the parameter table:  a confidence label, a reason, an
origin, and a contradicts entry for every parameter.  The gate asks the validator whether the file is
well formed, then reads the labels:

* a malformed file stops the run before anything runs;
* a `not_checked` row blocks a final run and only warns in a pilot run (docs/handoff-decisions.md, item 3);
* every `low` row and every recorded conflict is listed, so the Evaluator and both owners see them beside
  the verdict.  A `low` row never blocks, because a provisional assumption is allowed.

Three commands call the gate before they start:  `python -m harness` (a stage option), the history test
(always final, because it is one held-out run), and the trial batches (a required stage option).  The gate
lives here, beside the validator it wraps, so none of the three has to depend on another.

Whether a label is justified is a human judgment.  The gate checks the form and reports the labels; it
never decides that a source supports a claim.
"""

import csv
from pathlib import Path

from validators.handoff_hashes import file_sha256
from validators.parameters import validate_parameters

EVIDENCE_FILE = "data/parameters/evidence_columns_DRAFT.csv"
PARAMETERS_FILE = "data/parameters/iberian_lynx_baseline.csv"
SOURCES_FILE = "data/parameters/sources.csv"
STAGES = ("pilot", "final")


def check_repository(root, stage):
    """The gate for a command that runs outside the harness, on the research files under `root`."""
    root = Path(root)
    return check_evidence(root, root / PARAMETERS_FILE, root / SOURCES_FILE, stage)


def check_evidence(source_root, parameters, sources, stage):
    """Return (errors, report).  Errors reject the case; the report goes into case.json."""
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {', '.join(STAGES)}, not {stage!r}")
    report = dict(stage=stage, file=EVIDENCE_FILE, sha256=None, confidence={}, low=[], not_checked=[],
                  conflicts={}, warnings=[])
    path = Path(source_root) / EVIDENCE_FILE
    if not path.is_file():
        message = f"no evidence file at {EVIDENCE_FILE}"
        if stage == "final":
            return [f"final run refused: {message}"], report
        report["warnings"].append(f"{message} (a final run is refused without it)")
        return [], report
    problems = validate_parameters(parameters, sources, evidence=path)
    if problems:
        return ["evidence file failed validation: " + "; ".join(problems[:3])], report
    report["sha256"] = file_sha256(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        name, label = row["name"].strip(), row["confidence"].strip()
        report["confidence"][label] = report["confidence"].get(label, 0) + 1
        if label == "low":
            report["low"].append(name)
        entries = [entry.strip() for entry in row["contradicts"].split(";")]
        if entries == ["not_checked"]:
            report["not_checked"].append(name)
        elif entries != ["none_identified"]:
            report["conflicts"][name] = entries
    if report["not_checked"]:
        names = ", ".join(report["not_checked"])
        if stage == "final":
            return [f"final run refused: the contradiction check is not done for {names}"], report
        report["warnings"].append(f"the contradiction check is not done for {names} (a final run is refused)")
    return [], report
