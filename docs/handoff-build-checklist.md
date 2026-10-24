# Handoff build checklist (DRAFT)

Drafted 2026-10-22 by Valerie with Claude Code, from the tutor's feedback on the handoff lesson and from Anastasiya's skill file ("Multi-Agent System Skill File", shared in Slack on 2026-10-22 at 13:54 ET).  Status was checked against `develop` at `cc3b8fc` on 2026-10-22.  Owners are a proposal until Anastasiya agrees.

## Why

A handoff carries a task, scoped context, and partial results with their confidence.  The failures this list guards against are a payload that drops the confidence or the conflict, and a check that counts one claim twice.

## How to use it

Work from the top.  Close an item only with a test or a document change in the same pull request.  Every bar in this list is a guess until the first real runs measure it (item 6).

## The list

1. **Confidence per parameter.**  Add `confidence` and `confidence_reason` columns to the parameter CSV, and make the validator reject empty values.  Owner:  Valerie (data), Anastasiya (validator).  Enforced by:  CODE.  Status:  missing (the CSV has eight columns and neither).
2. **Independent origin per source.**  Add an `origin` column to `sources.csv` (the study a source repeats), and make the validator count two sources with one origin as one.  Owner:  Valerie (data), Anastasiya (validator).  Enforced by:  CODE.  Status:  missing.  Eight of 23 parameters list two or more source keys, and nothing says whether they are independent.
3. **Contradictions travel in the handoff.**  Add a `contradicts` column that names the parameters or sources in conflict, and move the conflicts from `docs/research-notes.md` into the table.  The validator rejects a name that does not exist.  Owner:  Valerie.  Enforced by:  CODE for the references; the Evaluator checks that every conflict in the notes has a link.  Status:  missing (range size and food; breeding age of 3 versus 2 years).
4. **A hand-back path.**  The Developer or the Evaluator files a typed request to the Researcher (parameter name, what is missing).  The harness allows one round per case, batches every open parameter, and stops and reports to both of us if one stays unresolved.  Open decision:  what happens when the batch exposes a new gap (proposal:  the case stops and reports; it never opens a second round).  Owner:  the pair, at the harness session.  Enforced by:  CODE (one budget counts every request, whoever files it).  Status:  missing (only Evaluator to Developer revision exists, 3 rounds).
5. **The harness computes the content hashes, never an agent.**  Owner:  the pair.  Enforced by:  CODE.  Status:  open decision (`docs/architecture.md`).
6. **Label every bar "guess" or "measured".**  This covers the eval plan, the baseline test, the sandbox limits (300 seconds, 10 MB), the history tolerance (0.05 and 10%), the trial counts (100 and 500), and the audit bar in item 7.  Re-ground each bar in the first real runs, and change a bar only in a commit that says why.  Owner:  Valerie.  Enforced by:  review.  Status:  partly (bars are written first; none is labeled).
7. **Human audit and two new planted flaws.**  Before each experiment batch, a person checks 10 random parameter rows against the primary source (bar:  9 of 10), and the team reads the total across batches, not one batch.  Add two flaws to `docs/baseline-test.md`:  a contradicting source dropped from the table, and two sources with one origin counted as two.  Owner:  Valerie.  Enforced by:  a person, plus the baseline test.  Status:  missing (the validator checks structure only).
8. **Count missed contradictions.**  Record in each trace every contradiction the Developer or the Evaluator finds that the table should have flagged.  A rising count means the Researcher misses quietly.  Owner:  Valerie.  Enforced by:  CODE (a trace field).  Status:  missing (`docs/trace-plan.md`).

## From Anastasiya's skill file

9. **A skipped required test is not a pass.**  `tests/test_handoffs.py` calls `pytest.importorskip("jsonschema")`, and the required `tests` check does not install `jsonschema`.  The CI log of 2026-10-22 shows "32 passed, 1 skipped", and the one skipped item is the whole handoff contract module.  Fix:  add `jsonschema` to `requirements-dev.txt` and replace `importorskip` with a plain import.  Ask Anastasiya first (her test file).  Owner:  the pair.  Enforced by:  CODE.  Status:  open.
10. **Bound transient retries apart from revisions.**  Revision rounds 0 to 3 are defined; a retry after a tool or network error is not.  Decide the number of transient retries (proposal:  1, a guess), count them apart from the revision rounds, and write each in the trace.  Owner:  the pair.  Enforced by:  CODE (harness).  Status:  missing.
11. **Each handoff has a valid example, an invalid example, the missing-data behavior, and the error output.**  `examples/handoffs/` holds valid examples only; the invalid cases sit inline in `tests/test_handoffs.py`.  Add the invalid examples and one line per handoff for missing data and for the error text.  Owner:  Anastasiya (schemas).  Enforced by:  CODE (tests).  Status:  partly.
