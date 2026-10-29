# Final report text without numbers (DRAFT)

Drafted 2026-10-25 by Valerie with Claude Code, for the report outline in `docs/report-skeleton.md`; the section numbers below are the numbers of that outline.  This file holds the sections that do not depend on a result:  the question, the system, the model, the evidence, the design of the grid and of the history test, and how to reproduce.  Every number that comes from a run is a blank marked **TO FILL**, with the file that supplies it.  Numbers that are design choices (the grid, the tolerances, the seeds) are written out, because they were fixed before any run.  Nothing here is a result, and nothing is agreed until Anastasiya has read it.

Section 1, the answer, is written last.  Section 8, what the model cannot tell us, stays in `docs/report-skeleton.md` (its limit 8 on the 2011 target is brought up to date in the same pull request as this file).  Each of us writes our own paragraph in section 10 in our own words.

## 1. Question and answer

How do food and usable habitat change whether a small Iberian lynx population survives for ten years in a simple model?  We ask it of a simulation of two patches with the biology of Doñana (Coto del Rey, 1992 to 2001), and we check the machinery against one historical record, the Andújar-Cardeña count from 2002 to 2011.  The prototype supports learning and the exploration of hypotheses.  It makes no forecast, and a pass of the history test does not validate the model.

**Answer in one sentence:**  TO FILL (after the final grid and the history test).

## 2. The system

Three roles prepare and check the work, and ordinary code joins them.

- **The Researcher** turns approved sources into a sourced parameter table.  It does not run the model, judge a result, or invent a source.
- **The Simulation Developer** runs the model on a validated input.  In this build it is a fixed `run_model` tool, not an agent that writes code (decision 4), so it cannot change the table or judge its own results.
- **The Evaluator** checks inputs, code, and results, and says pass, revise, or stop.  Its code checks decide the verdict; a model may only explain the issues in words (`docs/role-prompts.md`).
- **The harness** is ordinary code.  It validates the research files, takes a read-only snapshot with content hashes, compares the hashes at every handoff, limits revisions to three rounds, hands a gap back to the Researcher at most once, and writes one trace line for each step (`docs/harness-skeleton.md`, `docs/handback-path.md`).

The rule that shaped the design is in `AGENTS.md`:  a prompt asks, and code guarantees.  The design notes say which of the two enforces each rule, and a rule that only a prompt holds carries the tag PROMPT ONLY (the status tags of `docs/harness-skeleton.md`).

**TO FILL at the freeze:**  which parts ran live, which were tested only, and which were only planned, using the status tags of that day.

## 3. The model in one page

The model has two patches.  Each month, in this order:  survival, aging, dispersal and settlement, adult male movement, reproduction (in March only), and the record (`docs/model-conventions.md`).

- **Survival.**  An all-cause annual mortality of 0.37 for every animal except cubs, whose survival follows the cumulative values in the table (0.75 at 3 months, 0.69 at 10 months, 0.57 at dispersal).  The one mortality stands in for very different fates; it is a limit, not a measurement (limit 11 in `docs/report-skeleton.md`).
- **Dispersal and settlement.**  At 18 months an animal leaves its mother's range.  A female settles if her patch has a free territory, and the number of territories is the usable area divided by the female home range (10 km2 in the baseline), rounded down.  An unsettled female tries again every month, her current patch first and then the other, in a seeded random order (decided 2026-10-24; approved and merged in #49).
- **Reproduction.**  A settled female of breeding age breeds in March with probability 0.833 if a breeding-age male is in her patch and the spring rabbit density is at or above 4.6 per hectare.  A litter has two to four cubs.  The 4.6 cutoff is our assumption:  the monograph reports 4.6 and 1.0 rabbits per hectare as densities that were enough for lynx to breed, not as minimums (`docs/research-notes.md`).
- **Persistence.**  At month 120, a trial persists if a living breeding-age female holds a territory and a living breeding-age male is in the same patch.  The endpoint does not show long-term viability.

## 4. Evidence behind the parameters

Each parameter row of `data/parameters/iberian_lynx_baseline.csv` names its sources, and `data/parameters/sources.csv` says how each source was read:  in full, in part, in its abstract only, or not at all.  A value is no stronger than the way its source was read.  Reading the primary sources changed three things that secondary reports had stated more strongly:

- The EU report treated 1.0 and 4.6 rabbits per hectare as needed densities; the monograph says they were the lowest recorded and were enough, and it could not find the density at which lynx fail.
- The range-size result of Palomares 2001a rests on five ranges, with one female range inferred from male ranges.
- Pellet counts did not predict rabbit density well in scrubland (Palomares 2001b), and the one pellet-to-density conversion in Palomares 2001a has no verified origin.

As of 2026-10-29 (`develop` at 60e2ef6), by the `how_read` column of `sources.csv` (20 sources):  9 read in full (6 "full text read", 2 "full text", and 1 accepted manuscript read in full), 6 where the full text of a report's tables or of a news item was read (1, 4, and 1), 3 web pages, 1 with pages 1 to 3 read, and 1 "not read; named only".  The evidence file labels 23 parameters:  11 low, 12 medium, and 0 high, and the evidence gate counts 8 rows with a recorded conflict.  **Recount at the freeze** (2026-10-30), because both files can still change until then.

## 5. Main grid (design)

The start is 10 females and 10 males, five of each sex per patch, with ages drawn from 36 to 96 months.  The grid has three food levels (1, 4.6, and 55 rabbits per hectare) by two areas (each patch 50 or 100 km2), 120 months each.  A pilot runs 100 trials per cell and the final run 500; they are never mixed.  The outcomes are the share of trials that persisted (with a 95% Wilson interval), the final population, and the extinction time.

**TO FILL:**  the final table and figure from the 500-trial batch (`python -m report.figures batch.json --table table1.md --figure figure1.svg`), with the number of incomplete cells, if any, stated.

## 6. Sensitivity runs (design)

Reported apart from the main grid:  the rabbit threshold at 3.0 and 6.0; the female home range from 4 to 30 km2; the settlement-rule variants (own patch only, and one try only); and the linear breeding sensitivity beside the unchanged baseline (decision 3, never used to tune the history test).  The simulator has no option yet for the settlement variants or the linear sensitivity.

**TO FILL:**  which of them ran, and their results.

## 7. The history test

**Design, fixed before any run** (`docs/history-test.md`, `docs/history-preregistration.md`):

- The model starts from the 2002 Andújar-Cardeña count of 53 animals (25 adults and 28 non-adults) at a December census.
- Only the post-dispersal annual mortality is calibrated, from 0.10 to 0.50 in steps of 0.01, 100 trials per value, over months 0 to 96, so that the median growth is as near 1.17 a year as the grid allows.
- One held-out batch of 500 trials then runs to month 108, the 2011 census, at the calibrated mortality.  Nothing is retuned afterward.
- The pass requires the median growth inside 1.12 to 1.22 and the median 2011 count inside 181.8 to 222.2 (202 plus or minus 10%).  The target of 202 is the issuer's own figure (its 2011 and 2016 reports); the Cat Specialist Group's 214 is reported beside the verdict and never used for pass or fail.  Both owners agreed on 2026-10-25.
- The verdict uses the 750 km2 run only.  750 km2 stands in for the boundary of the park; it is not measured usable habitat.  The comparison runs use 264 km2 (the occupied area in 2010) at female home ranges of 6.1 and 10 km2.
- The run seed is 20261101, and each trial seed is the first 8 bytes of the SHA-256 of `run_seed|cell|trial`.

**Limits to say.**  Three anchor counts are all we hold, so a pass is weak evidence.  The 2011 count adds one year at the calibrated rate, so it is not independent of the calibration.  The start is partly assumed, and Doñana parameters are applied to Andújar-Cardeña.

**TO FILL after the run:**  the calibrated mortality; the median growth with its percentiles; the median 2011 count with its percentiles; the verdict, stated without adjusting any tolerance; the 214 comparison; the results of the 264 km2 runs and the calibrated mortality of each; and, if both owners agree, the territorial-female comparison (`docs/history-preregistration.md`, the row on the second observable).  Say plainly if the result is a fail.

## 8. What the model cannot tell us

See `docs/report-skeleton.md`, section "What the model cannot tell us".  Rewrite its numbers from the final run before the report goes out.

## 9. How to reproduce

- Python 3.12 in a fresh virtual environment, then `python -m pytest` (no key).  Python 3.12.15 was used on 2026-10-29, and 716 tests passed on `develop` at 60e2ef6.  **Recount at the freeze:**  the number grows as pull requests merge.
- The history test:  `python -m simulation.history --run-seed 20261101 --output history-run-1`.
- The batches:  `python -m simulation.experiments --preview --stage <pilot or final> --seed <seed> --trials <100 or 500> --months 120 --output <folder>`.  **TO FILL:**  the seeds.
- The report table and figure:  `python -m report.figures`.
- The harness:  `python -m harness --preview ...` offline; the live command is `python -m harness.live_case --preview --live --seed 7 --months 12 --output <folder>` (it needs the key and sends paid Claude requests; see `docs/live-workflow.md` and `docs/live-pass-runbook.md`).
- **TO FILL at the freeze:**  the commit hash of the code that produced every saved result and the hashes of the two research files (`docs/history-preregistration.md`).

## 10. What each of us did, and what the harness caught

**Shake-down of 2026-10-29 (a rehearsal on `develop` at 60e2ef6, not the final pass).**  The offline case passed in one attempt with no issues.  The scripted hand-back example stopped on its unresolved required gap (`female_home_range_km2`), as designed, and refused a second round.  The live case failed three times on the Researcher's second Claude call, because the model's hidden reasoning used the whole 1,200-token reply limit before any visible word; a fourth run, with the limit raised to 4,000 for that run only, passed with 6 of 12 Claude calls, all 12 code checks, and the evidence read check (the longest reply used 1,003 tokens).  The record is in `examples/shakedown_20261029/` (pull request #139), and the fix for the limit is pull request #136.

**How the harness and the roles behaved in the final live pass.  TO FILL after that pass:**  the case status and the number of attempts; the issues that the Evaluator raised and what the Developer changed; any retry and its reason; whether a hand-back round ran and how it ended; and what the traces show about the model's calls (`runs/<case>/trace.jsonl`, `case.json`).

**What the build caught.**  As of 2026-10-29 (`develop` at 60e2ef6), `docs/regressions.md` has 7 rows.  Two are caught by a test (the callback contracts, by `tests/test_harness_contracts.py`; the trace context, by `tests/test_trace_context.py`), one by a recorded contradiction entry in the evidence file (the EU report's misread densities; a test that the known conflicts are present is planned and not built), three still read "no test yet" (the stale status sentences, the approval given at an older commit, and the two values of the 2011 count), and one reads "no test" (food level 1 applied as a spring density, where the evidence text now says so).  The "dismiss stale approvals" setting that the approval row calls open was switched on for `main` on 2026-10-29.  Found on 2026-10-29 and not yet in that table, because their pull requests are open:  the live reply limit (#136), the hidden failure reason (#137), and two low-severity gaps from the red team (#138).

**Our own parts.**  Each owner writes this paragraph in their own words.  The record that it can draw on is the pull request list and `docs/regressions.md`; the pull request author is not a reliable sign of who did the work, because most pull requests were opened from one account.  **TO FILL:**  Anastasiya's paragraph; Valerie's paragraph.
