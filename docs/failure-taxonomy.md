# Multi-agent failure taxonomy: where Project Resurrection is exposed (DRAFT)

Drafted 2026-10-26 by Valerie with Claude Code, from LaNice's Learn slides "Multi-Agent Failure Taxonomy" (posted in the class channel on 2026-10-26).  The slides ask for three things:  trace what each agent received and sent, add a check at the riskiest handoff, and name which of the three multi-agent failures the design is most exposed to.  This file does all three, and says for each rule whether code enforces it today.

Status tags:  **CODE** (merged and tested), **IN REVIEW** (an open pull request), **PLANNED** (not built), **PROMPT ONLY** (the model is asked; nothing checks).  The tags are true on the day of this pull request.  Update them in the same pull request as the code that changes them.

## The answer first

We are most exposed to **cascading errors**, at the **Researcher to Developer handoff** (the parameter table and the source registry).  Three reasons:

1. It has already happened once.  `docs/regressions.md` (2026-10-24):  a secondary report's reading of 1.0 and 4.6 rabbits per hectare as needed densities was copied into our table as thresholds, and the monograph says they were the lowest densities recorded and were enough for reproduction, not needed densities (`docs/research-notes.md`, item 1).  Nothing looked broken; the table was wrong.
2. The checks on this handoff test structure, not truth.  `docs/parameter-validator.md`:  "These are structural checks, not proof that a source supports a claim."  Content hashes show that a file did not change, not that it was right.
3. Every later step trusts the table.  The Developer runs it, the Evaluator's code checks compare results with the same table, and a pass reads as polished.  Today the evidence file labels 11 of 23 parameters `low` and 12 `medium` (none `high`), and 8 carry a recorded conflict (`data/parameters/evidence_columns_DRAFT.csv`, on `develop` on 2026-10-26).  The model rule "no breeding below 4.6" is our assumption, not a finding (`docs/research-notes.md`, item 1).

Coordination breakdown and lost handoffs are the better covered of the three (rows below).  This ranking is our judgment from one regression row and the shape of the checks; it is not a measurement.

## The three failures, row by row

| Failure | How it could happen here | What catches it | Not caught yet |
|---|---|---|---|
| **Cascading errors** | A wrong or second-hand parameter flows from the Researcher to the Developer to the Evaluator and comes out as a confident pass | Hashes and unchanged-file checks (`check_handoff_hashes`, `check_files_current`):  **CODE**; the same checks inside the harness:  **CODE** (#74, merged 2026-10-26).  Evidence labels (confidence, origin, contradicts) checked for form by `python -m validators.parameters ... --evidence`:  **CODE**.  The Evaluator's code checks (`validators/results_checks.py`):  **CODE**.  Human review before anyone interprets findings:  **PROMPT ONLY** (a process rule in `docs/architecture.md`) | Until #86 merges, no command checks the evidence file, so `low` and `not_checked` do not warn or block.  The evidence gate in #86 covers the three ways to start a run (the harness, the history test, and the trial batches; **IN REVIEW**; the rule is `docs/handoff-decisions.md`, item 3).  The gate does not cover a single preview run by hand (`python -m simulation`), or a command that someone adds later without calling it  Planted flaws 4 (a double-counted cause of death) and 5 (history leakage) pass every code check (`docs/baseline-test.md` on #69, approved and not merged); only an arm that reads the table's notes or the history report can catch them (**PLANNED**) |
| **Coordination breakdown** | Two roles take the same step, each waits for the other, or a loop never ends | One owner per step and one writer of the shared state (`docs/architecture.md`):  design rule.  The harness, not an agent, makes the read-only snapshot (mode 444):  **CODE** (#74).  A cap of 3 revision rounds, a harness-side cap even if the Evaluator never says stop, and no retry after an error:  **CODE** (#74; tests `test_the_case_stops_after_round_3...`, `test_the_harness_caps_the_rounds...`).  One clarification round per case:  **CODE** (`harness/handback.py`) | No role calls a model yet, so no time limit on a call exists to test (**PLANNED** with the provider).  An identical result repeated across rounds is not detected early; the round cap ends it |
| **Lost in the handoff** | A constraint, a source, or the research question drops out between two roles | The three handoffs have schemas and examples (`schemas/`, `docs/agent-handoffs.md`):  **CODE**.  Files are named by content hash, so a table or source cannot be swapped without a mismatch:  **CODE** | No code checks that the task text matches the research question.  The Evaluator's report does not yet list every open conflict (**PLANNED**, `docs/handoff-decisions.md`); the labels live in the evidence file only |

## The trace:  what each agent received and sent

Each round saves `input.json`, `results.json`, and `evaluation.json`, and the trace adds one JSON line per step with the role, the tool, the input hashes, a summary of the result, and the validator verdict (`harness/trace.py`:  **CODE**, #74; the reading rules are in `docs/trace-plan.md`).  Text is cut at 400 characters and the cut is noted in `removed_text`; text that starts with `sk-` is redacted.  Gaps:  no role calls a model yet, so there are no prompts and `prompt_version` stays empty; the redaction pattern matches `sk-` strings only, so confirm the key format before the first live pass.

## The check at the riskiest handoff (BUILT, **IN REVIEW**:  #86)

The **evidence gate** (`validators/evidence_gate.py`, #86) sits between the Researcher and the Developer.  It runs before each of three commands:  `python -m harness` (the option `--stage pilot|final`, default `pilot`), `python -m simulation.history` (always final, because it is one held-out run, so there is no option to forget), and `python -m simulation.experiments` (a required `--stage`, no default).  Each does three things:

1. Pass the evidence file to the validator (`validate_parameters(..., evidence=...)`), so a malformed label stops the run before anything is written.
2. Refuse a final run when any parameter is `not_checked`; let a pilot run proceed with a warning.  This is the rule already written in `docs/handoff-decisions.md`, item 3.
3. Write every `low` parameter and every recorded conflict into `case.json`, so the Evaluator and both owners see them beside the verdict.

Tests that prove it (`tests/test_evidence_gate.py`):  a table with one `not_checked` row is rejected as a final run and warns as a pilot run; a malformed label rejects the case before the simulator runs; `case.json` lists the `low` and conflict rows and the file's hash.  Four mutation checks each make a test fail:  the grid's gate removed, `--stage` made optional again, the history test's gate removed, and the history test set to the pilot stage.  Two limits remain.  The grid's stage is stated by the person who runs it (nothing ties `--stage final` to 500 trials) and is not yet written into `batch.json`; recording it, with the evidence file's hash, is a small follow-up.  And a final run without an evidence file is refused (we propose yes after the freeze; an open decision for both owners).

## What this file does not show

Nothing here has run with a model.  Every **CODE** row is tested offline, so none of it shows that an agent obeys the rules that the code enforces.  The first live pass (proposed for Thursday 2026-10-29 in `docs/demo-plan.md`, #54) is the first test of these seams with real calls.
