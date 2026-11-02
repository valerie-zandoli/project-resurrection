# Final grid — pilot and final batches, 2026-11-02

Runner: Claude Code, at Valerie Zandoli's direct instruction, after Anastasiya Glegg named the seed in Slack (2026-11-02, 12:36 EST). Ran from commit `3355092`, code-identical to the frozen commit `0aee597` (no change to `simulation/`, `schemas/`, or `validators/` between the two). Python 3.12.15, seed 20261102. The freeze record lists Python 3.12.14; this run used the next patch release, 3.12.15, as both batch manifests record. The batch outputs are unchanged and were not rerun.

## What this is

The main grid of `docs/report-text.md` section 5: three food levels (1, 4.6, and 55 rabbits per hectare) by two areas (50 and 100 km2 per patch), 120 months each. A pilot ran 100 trials per cell; the final ran 500 trials per cell. Both completed with no incomplete cells.

## Result

| Food (per ha) | Area per patch (km2) | Trials | Persisted (95% interval) | Final population, median (10th to 90th) | Extinct | Median extinction month |
|---|---|---|---|---|---|---|
| 1.0 | 50 | 500 | 0.00 (0.00 to 0.01) | 0 (0 to 1) | 0.80 | 80 |
| 1.0 | 100 | 500 | 0.00 (0.00 to 0.01) | 0 (0 to 1) | 0.81 | 81 |
| 4.6 | 50 | 500 | 0.56 (0.51 to 0.60) | 13 (2 to 32) | 0.03 | 104 |
| 4.6 | 100 | 500 | 0.57 (0.52 to 0.61) | 13 (2 to 31.1) | 0.03 | 107 |
| 55.0 | 50 | 500 | 0.57 (0.53 to 0.61) | 14 (1 to 32) | 0.06 | 104 |
| 55.0 | 100 | 500 | 0.57 (0.53 to 0.61) | 13 (2 to 32) | 0.04 | 101 |

The pilot (100 trials per cell) showed the same pattern before the final batch ran, so the final numbers are not a surprise relative to the pilot.

## Limits (from the protocol, `docs/report-text.md` section 5 and 8)

- Food below 4.6 per hectare is below the breeding threshold in this model, so persistence is effectively zero at the 1.0 level; this is an assumption (the 4.6 cliff), not a measured breeding-failure point.
- Food above 4.6 is treated as one level by the model's breeding rule, so this grid cannot tell 4.6 and 55 apart on breeding alone; the small remaining difference between those two rows reflects trial noise, not a modeled effect of food beyond the threshold.
- Area matters only through the number of territories it creates (area divided by the female home range), not through any other effect.
- Persistence means a living breeding-age female holds a territory and a living breeding-age male shares her patch at month 120; it is not a long-term viability claim.
- This grid does not use or depend on the history test's calibrated mortality or its held-out result; the two are independent pieces of evidence.

## Seed

20261102 (today's date), chosen over 42 because it follows the same convention as the history test's own seed (20261101, fixed the day the pre-registration was written). Chosen by Anastasiya in Slack before this batch ran; not changed after seeing a result.

`batches/pilot/batch.json` and `batches/final/batch.json` are the unchanged outputs of `python -m simulation.experiments --preview --stage pilot|final --seed 20261102 --trials 100|500 --months 120 --output <folder>`. `batches/final/table1.md` and `batches/final/figure1.svg` are the unchanged outputs of `python -m report.figures batches/final/batch.json --table batches/final/table1.md --figure batches/final/figure1.svg`. It ran locally without Claude or network calls.
