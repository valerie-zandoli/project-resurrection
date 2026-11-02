# Final historical comparison — first held-out run, 2026-11-02

Runner: Anastasiya Glegg, assisted by Codex. Freeze PR #144 was confirmed merged before execution. The run used a clean detached checkout of the frozen executable commit `0aee597fa2229a6cb97bf057de5f26d9ae8d8328`, Python 3.12.14, seed 20261101, and the exact normalized parameter/source hashes in the freeze record. No final run was repeated and no parameter was changed after the result was seen.

## Result

Both preregistered checks passed for the main 750 km² arm. Calibration selected 17% post-dispersal annual mortality. Held-out median annual growth: 1.16833596055421 (bounds 1.12–1.22). Median 2011 population: 217 (target 202; bounds 181.8–222.2), about 7.43% above the target. The 10th–90th percentile population range was 152–288.1; the acceptance criterion is the median, not that whole range.

Each of the three agreed arms ran the complete 41-setting × 100-trial calibration and 500-trial held-out batch. Only the primary 750 km² arm determines pass/fail. The two 264 km² arms are sensitivity results, not additional acceptance tests.

Territorial females remain report-only: main-run medians 27 in 2010 and 33 in 2011, alongside census values 43 and 51. No tolerance or pass/fail was assigned to that observable.

## Limits (preserved from the protocol)

- Three counts (2002, 2010, 2011) are all we hold, so a pass is weak evidence.
- Donana parameters are applied to Andujar-Cardena (a transfer assumption).
- The starting population is an assumption except the two counts:  12 or 13 adult females, adult ages 36 to 108 months, non-adult ages 0 to 35 months, cub sex ratio of the table.
- The census date is assumed to be the end of the year (month 0 is a December).
- The usable area is an assumption (750 km2 for the main run); the verdict uses the main run only.  The 264 km2 arms use female home ranges of 6.1 and 10 km2 and are reported beside it.
- The 2011 target of 202 is the issuer's own figure (its 2011 and 2016 reports); 214 (Cat Specialist Group) is reported beside it and never used for pass or fail.
- The 2011 count adds one year at the calibrated rate; it is not independent of the calibration.
- Territorial females (43 in 2010 and 51 in 2011) are reported beside the verdict for the 750 km2 run only, as the median number of settled females of breeding age with the 10th and 90th percentiles; there is no tolerance and no pass or fail, and we do not call it support or failure.  The 264 km2 arms hold fewer territories than the census counts, so their numbers are marked capacity-limited and are not compared.

This is a pass of the agreed limited historical test, not broad scientific validation or a conservation recommendation. It does not change the synthetic experiment defaults. Earlier development calibration remains separately labelled.

`report.json` is the unchanged first report. `execution.json` records start/end UTC, runner, Python, frozen code and freeze merge identities. The command equivalent was `python -m simulation.history --run-seed 20261101 --output NEW_DIRECTORY`, using all default arms/trial counts. It ran locally without Claude or network calls.
