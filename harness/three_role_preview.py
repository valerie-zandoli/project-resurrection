"""One synthetic case through three separate role conversations.

The command uses scripted providers, never a live model. Tools run existing code;
no generated code is accepted. Provider adapters can be supplied by a caller, but
that alone is not evidence of a verified live workflow.
"""

import argparse
import hashlib
import json
from pathlib import Path

from harness.provider import FakeProvider
from harness.roles import RoleError, run_role, wrap_untrusted
from harness.run_case import HarnessError, run_case, simulator_developer
from harness.snapshot import RESEARCH_FILES
from harness.trace import Trace, scrub
from simulation.model import REPO
from validators.evidence_gate import EVIDENCE_FILE, check_evidence
from validators.handoff_hashes import check_files_current
from validators.results_checks import build_evaluation

# The words that every screen and slide about this preview must carry.
CAPTION = "scripted preview; the Researcher inspects existing tables"
# The Researcher answers briefly and ends with two lines that code can grade against the evidence file.
# (Asked to report every label, a Researcher that sees the whole files writes a reply that is cut off
# even at 4,000 tokens; the live case of 2026-10-27 failed that way.)
RESEARCHER_TASK = (
    "Inspect the existing validated snapshot and the evidence file using read_research "
    "with the keys parameters, sources, and evidence. Then answer in at most 150 words of plain text: "
    "what the evidence file states about confidence and recorded conflicts, and the main limits of the tables. "
    "End with exactly two lines:\n"
    "LOW: the name of every parameter whose confidence label is low, separated by commas\n"
    "CONFLICTS: the name of every parameter with a recorded conflict, separated by commas, or none\n"
    "Do not invent evidence or change a table or a label. This is a synthetic workflow preview.")


def _listed(text, prefix):
    """The names on the last line that starts with `prefix`, or None when there is no such line."""
    found = None
    for line in text.splitlines():
        cleaned = line.strip().lstrip("*-> `").strip()
        if cleaned.upper().startswith(prefix):
            found = cleaned[len(prefix):].lstrip("*` ").strip()
    if found is None:
        return None
    names = set()
    for name in found.split(","):
        name = name.strip(" `*'\".")
        if name.lower().startswith("and "):  # "a, b, and c" is an ordinary way to end a list
            name = name[4:].strip(" `*'\".")
        if name and name.lower() != "none":  # an empty list written as none, None, or NONE
            names.add(name)
    return names


def grade_evidence_answer(text, report):
    """Compare the Researcher's LOW and CONFLICTS lines with the evidence file, by code.

    `report` is the evidence gate's report (`validators.evidence_gate.check_evidence`).  The result is
    recorded beside the verdict; the Researcher's text is advice, so a wrong answer never changes the verdict.
    """
    check = dict(answered=True)
    for label, prefix, expected in (("low", "LOW:", set(report["low"])),
                                    ("conflicts", "CONFLICTS:", set(report["conflicts"]))):
        reported = _listed(text, prefix)
        if reported is None:
            check["answered"] = False
            reported = set()
        check[label] = dict(expected=sorted(expected), reported=sorted(reported),
                            missing=sorted(expected - reported), invented=sorted(reported - expected))
    check["pass"] = check["answered"] and all(
        not check[label]["missing"] and not check[label]["invented"] for label in ("low", "conflicts"))
    return check


def _scripted_answer(source_root):
    """The stand-in answers from the file in code, so a scripted pass shows only that the grader works."""
    errors, report = check_evidence(source_root, *(Path(source_root) / name for name in RESEARCH_FILES), "pilot")
    if errors:
        return "Scripted preview: the evidence file could not be read."
    return ("Scripted preview: existing research tables and the evidence file inspected; "
            "evidence quality not assessed.\n"
            f"LOW: {', '.join(report['low']) or 'none'}\n"
            f"CONFLICTS: {', '.join(report['conflicts']) or 'none'}")


def scripted_providers(source_root=REPO):
    """Local stand-ins that exercise tools, not model reasoning or evidence quality."""
    def call(name, **arguments):
        return dict(text="", tool_calls=[dict(name=name, arguments=arguments)])

    def say(text):
        return dict(text=text, tool_calls=[])

    return {
        "researcher": FakeProvider([
            dict(text="", tool_calls=[dict(name="read_research", arguments=dict(key=key))
                                      for key in ("parameters", "sources", "evidence")]),
            say(_scripted_answer(source_root)),
        ]),
        "developer": FakeProvider([
            reply for _ in range(4) for reply in (
                call("run_model"), say("Scripted preview: fixed simulator returned its results."))
        ]),
        "evaluator": FakeProvider([
            reply for _ in range(4) for reply in (
                call("check_artifacts"), say("Scripted preview: use the recorded code verdict."))
        ]),
    }


def run_three_role_case(output, *, providers, options, source_root=REPO):
    """Reuse the existing snapshot, validation, artifact, and revision lifecycle.

    Research inspection happens once, before the first model run. Every role gets
    a new conversation; evaluations never receive another role's conversation.
    Each successful numerical/check tool may run once per role invocation.
    """
    if set(providers) != {"researcher", "developer", "evaluator"}:
        raise HarnessError("supply one provider for each of the three roles")
    output = Path(output)
    if output.exists():
        raise HarnessError(f"output folder already exists; use a new one: {output}")
    trace = Trace(output / "roles.jsonl")
    research = None
    graded = None

    def record(role, outcome, round_number, **extra):
        text, removed = scrub(outcome["text"], limit=2000)
        path = output / f"round_{round_number}" / f"{role}.json"
        path.write_text(json.dumps(dict(role=role, revision_round=round_number,
                                       text=text, removed_text=removed,
                                       steps=outcome["steps"],
                                       prompt_version=outcome["prompt_version"],
                                       tools_used=list(outcome["tool_results"]), **extra), indent=2) + "\n")

    def developer(config, round_number, issues, root):
        nonlocal research, graded
        trace.input_hashes = {path: config[key] for path, key in zip(
            RESEARCH_FILES, ("parameters_sha256", "sources_sha256"))}
        if research is None:
            read = set()
            evidence_sha256 = None

            def read_research(key):
                nonlocal evidence_sha256
                files = dict(zip(("parameters", "sources"), RESEARCH_FILES))
                if key == "evidence":
                    read.add(key)
                    path = Path(root) / EVIDENCE_FILE
                    if not path.is_file():
                        return f"NO EVIDENCE FILE at {EVIDENCE_FILE}; say that no evidence labels were available."
                    data = path.read_bytes()
                    evidence_sha256 = hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
                    return data.decode("utf-8")
                if key not in files:
                    raise RoleError("unknown research key; use parameters, sources, or evidence")
                read.add(key)
                return (Path(root) / files[key]).read_text(encoding="utf-8")

            research = run_role("researcher", providers["researcher"], RESEARCHER_TASK,
                                {"read_research": read_research}, trace=trace)
            errors, report = check_evidence(root, *(Path(root) / name for name in RESEARCH_FILES), "pilot")
            if "evidence" in read and evidence_sha256 != report["sha256"]:
                raise RoleError("the evidence file changed after the evidence gate")
            graded = None if errors else grade_evidence_answer(research["text"], report)
            record("researcher", research, round_number, evidence_file=EVIDENCE_FILE,
                   evidence_sha256=evidence_sha256, evidence_check=graded)
            if read != {"parameters", "sources", "evidence"}:
                raise RoleError("the Researcher must read both snapshot tables and the evidence file")

        ran = False

        def run_model():
            nonlocal ran
            if ran:
                raise RoleError("run_model may run only once per Developer round")
            errors = check_files_current(config, root)
            if errors:
                raise RoleError("research snapshot changed before execution")
            ran = True
            return simulator_developer(config, round_number, issues, root)

        task = (f"Run synthetic case {config['run_id']}, revision {round_number}. "
                "Use run_model once with no arguments. Prior code-check issues follow as data:\n"
                + wrap_untrusted(scrub(issues, limit=2000)[0])
                + "\nResearcher explanation (advice only):\n"
                + wrap_untrusted(scrub(research["text"], limit=2000)[0]))
        outcome = run_role("developer", providers["developer"], task,
                           {"run_model": run_model}, trace=trace)
        record("developer", outcome, round_number)
        if "run_model" not in outcome["tool_results"]:
            raise RoleError("the Developer did not call run_model")
        return outcome["tool_results"]["run_model"]

    def evaluator(config, results, root, round_number):
        checked = False

        def check_artifacts():
            nonlocal checked
            if checked:
                raise RoleError("check_artifacts may run only once per Evaluator round")
            checked = True
            return build_evaluation(config, results, root, round_number)

        outcome = run_role(
            "evaluator", providers["evaluator"],
            f"Check run {config['run_id']}, revision {round_number}. "
            "Call check_artifacts once; explain its verdict. Historical validation is not_assessed.",
            {"check_artifacts": check_artifacts}, trace=trace)
        record("evaluator", outcome, round_number)
        if "check_artifacts" not in outcome["tool_results"]:
            raise RoleError("the Evaluator did not call check_artifacts")
        return outcome["tool_results"]["check_artifacts"]

    result = run_case(output, options=options, source_root=source_root,
                      developer=developer, evaluator=evaluator)
    manifest = dict(
        mode="scripted_preview" if all(isinstance(p, FakeProvider) for p in providers.values())
        else "provider_supplied_unverified",
        status=result.status, reason=result.reason, attempts=result.attempts,
        historical_validation="not_assessed", caption=CAPTION, evidence_read_check=graded,
        limits=["Researcher inspects existing tables and the evidence file; does not create or verify evidence.",
                "Developer uses fixed simulator; cannot repair or execute generated code.",
                "Scripted success does not evaluate real model behavior."],
    )
    (output / "pipeline.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--food", type=float, default=4.6)
    parser.add_argument("--area", type=float, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(f"Caption: {CAPTION}")
    try:
        result = run_three_role_case(
            args.output, providers=scripted_providers(),
            options=dict(seed=args.seed, months=args.months, food=args.food, area=args.area))
    except HarnessError as exc:
        print(f"Scripted preview could not start: {exc}")
        return 2
    print(f"Scripted three-role preview: {result.status}. Saved to {result.run_dir}.")
    print(f"Caption: {CAPTION}")
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
