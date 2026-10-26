# Plan for the demonstration on Monday 2026-11-02 (PROPOSED)

Written 2026-10-24 by Valerie with Claude Code.  Everything here is a proposal until Anastasiya says yes; the presenter split and the times are not agreed.

## What the dates force

- LaNice said on 2026-10-24 that the issued API keys last for the whole project and end after the presentation.  The hour of expiry is unknown, so no step on 2026-11-02 may depend on the key.
- The simulation needs no key.  Only live role-agent calls do, so any live call must be recorded before the demonstration.

## Timeline

| Date | What |
|---|---|
| Mon 2026-10-26 | Anastasiya presents the design plan.  Tuesday 09:30 ET:  key check (reminder set). |
| by Wed 2026-10-28 | The open decisions that change the contract or the parameter table are made (the 2011 target, the area, the retry rule, the thresholds), so the freeze below freezes the final versions. |
| Thu 2026-10-29 | Freeze the contract and the parameter table (a change after this date means a new run ID and a re-run of every saved result). |
| by Fri 2026-10-30, 18:00 ET | Every run that needs the key is finished and saved against the frozen version:  the history test, the pilot and final grid, one live pass through the three roles, and one hand-back example. |
| Sat 2026-10-31 | Draft the report from the saved files. |
| Sun 2026-11-01, 09:30 ET | Key check (reminder set); full rehearsal with a timer. |
| Mon 2026-11-02 | The demonstration. |

## The demonstration, in order

1. The question and the plan (slides 1 and 2).
2. The three roles and the handoffs, with the diagram (slides 2 and 3).
3. What is real today:  tested only, planned, prompt only (slide 5), updated to the day's truth.
4. One recorded run:  `input.json`, `results.json`, `evaluation.json`, and the Evaluator's issues.
5. One hand-back example:  a request, the single round, and the stop on an unresolved required gap.
6. The history test:  the calibrated mortality, the held-out medians against the bounds, and the limits.
7. The grid:  persistence by food and area, with intervals, and what the model cannot tell us.
8. What stays open.

## The fallback, which does not need the key

Keep these in the repository (or a linked release) before 2026-11-01:  the history report (`report.json`), the batch files and summaries of the pilot and final grid, one saved `results.json` with its `evaluation.json`, the saved traces of the live pass, and the slide PDF.  If a live call fails, say so and show the saved file; do not retry in front of the audience.

## The report outline

Follow `docs/history-test.md` ("The report must say") and `docs/model-conventions.md` section 4.  For each cell:  persistence share with a 95% Wilson interval; median final population with the 10th and 90th percentiles; share of trials that went extinct; median extinction month among them.  Then the history result with its limits (three counts, transferred Donana parameters, assumed start, census date, and usable area); the labels (tested only, planned, prompt only); the sources read in full and the sources not (`docs/unread-sources.md`); and every open decision.

## To agree

Who presents which part on 2026-11-02; the length of the slot; whether the demonstration is live, recorded, or both; the contract-freeze date (proposed Thu 2026-10-29, so that every saved result matches what we present; Anastasiya's suggestion of 2026-10-25).
