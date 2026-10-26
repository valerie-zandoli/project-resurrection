# Model conventions to settle before experiments (PROPOSED)

Drafted 2026-10-22 by Valerie with Claude Code.  These are the details that the agreed simulator rules leave open:  the order of events in a month, how a litter is sampled, the historical starting structure, and how trials are combined.  Each is a convention, not a measurement.  Nothing here is agreed until Anastasiya says yes, and nothing is built.

## 1. Order of events in one month

1. **Survival.**  Every living animal faces its monthly risk:  cubs by the monthly rates from the cumulative values (0.75 at 3 months, 0.69 at 10 months, 0.57 at dispersal), everyone else by (1 - m) ^ (1 / 12), where m is the active `annual_mortality_rate_all_causes` (baseline 0.37; the sensitivity runs and the historical calibration set it between 0.10 and 0.50).
2. **Aging.**  Every survivor becomes one month older.
3. **Dispersal and settlement.**  Animals that reach the dispersal age (18 months) leave their mother's range.  A female settles if her patch has a free territory slot (usable area divided by the female home range, rounded down; the baseline home range is 10 km2, and the home-range sensitivity runs of 4 to 30 km2 override it); otherwise she stays alive and unsettled, under the same all-cause mortality.  **Retries:**  every month, in this step, each female that is old enough to settle and is still unsettled tries again, her current patch first and then the other patch, and she settles in the first patch that has a free slot.  When more females want a free slot than there are slots, a seeded random order decides (one shuffle per month, from the run seed).  The monthly retry, the patch choice, and the order are conventions to agree, not measured facts.

**Decision (2026-10-24):**  Valerie chose this rule for the main grid and the history test:  every month, each unsettled female of at least 18 months tries again, her current patch first and then the other, in one seeded random order per month.  Anastasiya approved and merged it in #49 on 2026-10-25.  Two other rules run as sensitivity checks, reported apart from the main grid:  **own patch only** and **one try only** (at the dispersal age).  The preview now exposes these as separate run settings; their implementation does not confirm the main rule or establish which rule real lynx follow.

For the one-try sensitivity, the preview interprets one try as checking the female's current patch and then the other patch once, in the month she first reaches dispersal age.  If both patches are full, she stays unsettled and does not retry.  A female who is already older than the dispersal age and unsettled when a run starts never gets her try.  The synthetic grid starts every female settled, so this does not touch it; the history-test start has unsettled non-adult females aged 18 to 35 months, so a one-try history run would never settle them.  This operational detail is recorded for review and remains a modeling convention.

**Why this rule:**  a one-off preview check on 2026-10-24 compared six rules (the three above, plus a retry every 3 months, once a year, and oldest female first) over 300 seeded trials each, 120 months, food 4.6, the synthetic 20-lynx start.  The share of trials that persisted was 0.52 to 0.60 for every rule except one try only at 50 km2 per patch (0.47); the other differences are within the noise of 300 trials (about plus or minus 0.06).  So the choice barely moves the result, and the rule that the code, the tests, and `docs/simulator.md` already use is the simplest to keep.  This check is not a historical test and kept no script.
4. **Adult male movement.**  Each adult male crosses to the other patch with probability 0.10.  Males use no female slots.
5. **Reproduction,** in the birth month only (March).  A female breeds if she is settled, aged from `breeding_age_min` to `breeding_age_max`, in a patch with an eligible male, and the spring rabbit density is at or above the threshold (baseline 4.6 per hectare; the threshold sensitivity runs use 3.0 and 6.0).  She then breeds with probability 0.833.
6. **Record** the month's counts, births, deaths, and moves.

Why this order:  births come last, so a newborn faces its first risk in the next month and is not counted dead before it is counted born.  The alternative (reproduction before survival) lets a female that dies in March still give birth.  Choose one and keep it; the history test is sensitive to the choice, so run the other order once as a sensitivity check.

## 2. Litter size

The table gives a mean of 3.0 with a range of 2 to 4, from litters seen before 4 weeks, and no distribution.  Convention:  draw the litter size uniformly from the integers 2, 3, and 4 (mean 3.0, the whole published range).  A fixed litter of 3 is a sensitivity run.  Each cub is female with probability 1.03 / (1 + 1.03) = 0.507.

## 3. Historical starting structure

See `docs/history-test.md`:  25 adults and 28 non-adults, with the age and sex rules in that file.  Both are assumptions.  The synthetic runs use 10 females and 10 males with ages drawn uniformly from 36 to 96 months, five of each sex per patch.

## 4. Combining trials

- Each cell (food level by usable area) runs 100 trials as a pilot and 500 as the final.  Pilot results are never mixed into final results.
- Seeds:  each trial's seed comes from the run seed, the cell name, and the trial number, by one documented rule, so any single trial can be replayed.
- Per trial the model records endpoint persistence (yes or no), the final population, and the extinction month (empty, not 120, when the population survives).
- Per cell the report gives the share of trials with persistence and its 95% interval (Wilson), the median and the 10th to 90th percentile of the final population, the share of trials that went extinct, and the median extinction month among those that did.
- No trial is selected, trimmed, or re-run because of its outcome.
- A simulation defect (a crash, a failed model check, or a killed run) is never retried and never dropped.  The trace keeps the failed attempt and its seed, the trial stays in the cell's denominator as "failed", and the cell stops at the first such defect and is reported as incomplete, never summarized as if it were complete.
- Only a transient tool or provider error (a network timeout, HTTP 429, or HTTP 5xx) is retried, under the limits in `docs/handoff-decisions.md` (1 per call, 3 per round, 10 per case).
- The sensitivity runs (rabbit thresholds 3.0, 4.6, and 6.0; female home range 4 to 30 km2) are reported apart from the main grid.
