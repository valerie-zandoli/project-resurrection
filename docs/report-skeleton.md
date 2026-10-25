# Final report skeleton (DRAFT)

Drafted 2026-10-24 by Valerie with Claude Code.  This file fixes the outline of the final report, says where each table and figure comes from, and drafts the section on what the model cannot tell us.  It holds no result.  Every number below comes from the synthetic preview (seed 20261025, 100 trials per cell, 120 months, unless it says 300) and is marked as such.  Files tagged (in review) exist only in open pull requests until those merge:  #50 history code, #51 Evaluator checks, #56 harness and diagram, #57 research notes, #61 regressions, #62 pre-registration.

## Outline

1. **Question and answer in one paragraph.**  What the model asks (does a small Iberian lynx population persist for 120 months, and under which food and area assumptions) and the one-sentence answer.  Write this last.
2. **The system in one picture.**  `docs/diagrams/architecture-v3.svg` (in review, #56) and a half-page on the three roles and the harness.  Say which parts run today and which are only tested.
3. **The model in one page.**  The agreed rules from `docs/prd.md` and `docs/model-conventions.md`; the persistence endpoint; the order of events in a month.
4. **Evidence behind the parameters.**  The parameter table (`data/parameters/iberian_lynx_baseline.csv`) and its source list (`data/parameters/sources.csv`), with each value tagged as read in the source, read in an abstract only, or our assumption.
5. **Main grid.**  Persistence share with 95% intervals by food level and area (table and figure below); final population; extinction share.
6. **Sensitivity runs,** reported apart from the main grid:  rabbit threshold 3.0, 4.6, 6.0; female home range 4 to 30 km2; settlement rule variants.
7. **History test.**  Pre-registered in `docs/history-preregistration.md` (in review, #62); one held-out run; pass or fail stated without adjusting the tolerances.
8. **What the model cannot tell us.**  Drafted below.
9. **How to reproduce.**  Commands, seeds, code hash, Python version.
10. **What each team member did,** and what the harness caught during the build (from `docs/regressions.md`, in review, #61).

## Where each piece comes from

| Piece | Source | Command |
|---|---|---|
| Table 1, main grid | `batch.json` from the final run | `python -m report.figures batch.json --table table1.md` |
| Figure 1, persistence with intervals | the same file | `python -m report.figures batch.json --figure figure1.svg` |
| History test result | the history test output (in review, #50) | see `docs/history-test-code.md` once #50 merges |
| Evaluator verdicts per case | `case.json` and `trace.jsonl` of each harness run (in review, #56) | see `docs/harness-skeleton.md` once #56 merges |

The report code never overwrites a file and never prints an incomplete cell as a number; it marks the cell "incomplete" with its status.

Example of the table (synthetic preview, not a result):

| Food (per ha) | Area per patch (km2) | Trials | Persisted (95% interval) | Final population, median (10th to 90th) | Extinct | Median extinction month |
|---|---|---|---|---|---|---|
| 1.0 | 50 | 100 | 0.00 (0.00 to 0.04) | 0 (0 to 1) | 0.78 | 82 |
| 1.0 | 100 | 100 | 0.00 (0.00 to 0.04) | 0 (0 to 1) | 0.80 | 77.5 |
| 4.6 | 50 | 100 | 0.58 (0.48 to 0.67) | 13 (2.9 to 31.1) | 0.05 | 101 |
| 4.6 | 100 | 100 | 0.60 (0.50 to 0.69) | 12.5 (2 to 33) | 0.03 | 100 |
| 55.0 | 50 | 100 | 0.68 (0.58 to 0.76) | 14.5 (3 to 30.2) | 0.03 | 108 |
| 55.0 | 100 | 100 | 0.49 (0.39 to 0.59) | 11 (1 to 35) | 0.06 | 110.5 |

## What the model cannot tell us (draft for section 8)

Each limit has the evidence in this repository.  Rewrite the numbers from the final run before the report goes out.

1. **It cannot tell food levels at or above 4.6 apart.**  The model treats every level at or above the 4.6 per hectare threshold the same, so food 4.6 and food 55 differ only by sampling noise.  In the preview, the persistence shares at 50 km2 are 0.58 and 0.68, and at 100 km2 they are 0.60 and 0.49; the intervals overlap and the direction reverses.  A gap between those cells is not a finding.
2. **The cliff at 4.6 is our assumption, not a measurement.**  The monograph reports 4.6 and 1.0 rabbits per hectare as densities where lynx do well, not as minimums for breeding (`docs/research-notes.md`, in review, #57).  Extinction at food 1 follows from the rule that no female breeds below the threshold; the model cannot say what lynx do at 2 or 3 rabbits per hectare.
3. **It cannot tell 50 km2 from 100 km2 per patch.**  Only the number of female territories matters to the model (usable area divided by the home range).  The preview shows no consistent area effect, but a modest one could hide inside the noise of 100 trials (about 0.1 either way, about 0.04 at 500).
4. **Persistence mixes extinction with a missing pair.**  The endpoint needs a living breeding-age female with a territory and a living breeding-age male in the same patch at month 120.  In the preview, most trials that fail persistence are still alive:  at food 4.6 and 50 km2, 0.58 persisted, 0.05 went extinct, and so 0.37 were alive but without a qualifying pair (computed from the table).  In the 300-trial re-run of 2026-10-24, about 20% and 14% of trials were alive but missing a breeding-age female or a breeding-age male, against 3 to 4% extinct.  Report births in the last 12 months beside persistence, as `docs/prd.md` asks.  The endpoint does not show long-term viability.
5. **The start is synthetic.**  The batch runs start from 20 lynx with ages drawn uniformly from 36 to 96 months; the history test starts from 53 lynx split 25 and 28 by an age rule we chose.  Both are assumptions.
6. **Habitat and disease are fixed.**  Rabbit density is constant within a run; there is no disease, no change in habitat quality, no inbreeding, and no management action.  A wild population meets all four.
7. **The parameters travel from one population to another.**  Reproduction and cub survival come from Donana (1992 to 2001); the history test compares against Andujar-Cardena (2002 to 2011).  The match of the two is a transfer assumption (`docs/history-test.md`).
8. **The history test has three anchor counts.**  A pass is weak evidence and a fail cannot say which rule is wrong.  The 2011 target is also unsettled (214 or 202; see `docs/research-notes.md`).
9. **The settlement rule changes little, so the model cannot say which rule lynx follow.**  Monthly retries, patch order, and the seeded shuffle are conventions (`docs/model-conventions.md`).  In the 300-trial re-run of 2026-10-24, persistence stayed between 0.52 and 0.60 for every retry variant except "one try only" at 50 km2 (0.47), and releasing old females' territories changed nothing.  That is a statement about this model, not about lynx.
10. **Several sources are read only in abstract.**  The registry tags them; any value that rests on one is no stronger than its tag.

## To fill after the final run

- Main grid table and figure from the 500-trial final batch.
- The history result, the 2011 target, and the file hashes from `docs/history-preregistration.md`.
- The code hash and Python version printed in `batch.json`.
- The one-paragraph answer (section 1).
