# History test code (PROPOSED)

Written 2026-10-24 by Valerie with Claude Code.  The code is `simulation/history.py`; its tests are `tests/test_history.py`.  It implements `docs/history-test.md`.  Nothing here is agreed until Anastasiya says yes, and the held-out batch has not been run.

## What the code fixes, so that a run cannot change it

- **The two tolerances:**  median growth 1.12 to 1.22, median 2011 count 192.6 to 235.4, both bounds inclusive.  A test reads `data/history/counts.csv` and checks that the numbers match the counts (53, 25, 190, 214).
- **The stopping point:**  calibration runs 96 months (the 2010 census) and stops, so it never computes the 2011 count.  A test fails if calibration simulates past month 96.
- **The one parameter that changes:**  post-dispersal annual mortality, from 0.10 to 0.50.  Every other parameter stays at its baseline.
- **The seed rule:**  each trial's seed is the first 8 bytes of SHA-256 of `run_seed|cell|trial`, read as an integer.  The cell is `calibration-m<mortality>` or `heldout`.  Tests fix two example values, show that no held-out seed appears in calibration, and show that the held-out batch uses only held-out seeds.
- **The frozen batch:**  the held-out batch takes the calibrated mortality and nothing else changes.  The run refuses an output directory that exists, so a second look needs a new directory and a reason.

## The choices that the documents leave open (all assumptions)

| Choice | Value | Why |
|---|---|---|
| Census month | month 0 is a December; months 96 and 108 are also Decembers | The 2010 census was taken at the end of the year (`efe_2011_01`). |
| Start, adults | 25, ages 36 to 108 months uniform; 12 or 13 females, decided by the seed | `docs/history-test.md`. |
| Start, non-adults | 28, ages 0 to 35 months uniform; female with probability 1.03 / 2.03 | `docs/history-test.md`. |
| Start, patches | animals alternate between two equal patches; adult females start settled | The simulator has two patches. |
| Usable area | total area split equally over two patches; the areas run are 750 (main), 500, and 1,000 km2 | Decided 2026-10-24 (the main run) with sensitivity runs. |
| Food | 4.6 rabbits per hectare | Breeding needs at least the spring threshold; any value at or above it gives the same run. |
| Mortality grid | 0.10 to 0.50 in steps of 0.01 (41 values) | The range is agreed; the step is a choice. |
| Calibration trials | 100 per mortality value | The pilot size of `docs/model-conventions.md`. |
| Held-out trials | 500 | The final size of `docs/model-conventions.md`. |
| Extinct trial | counts as growth 0 in the median | A trial with no animals at month 96 has no growth. |
| Pass | both medians inside their bounds on the held-out batch | The calibrated growth alone cannot pass the test. |
| Main run | the verdict uses the 750 km2 run only | Decided 2026-10-24; the 500 and 1,000 km2 runs sit beside it. |

## How to run it

```bash
python -m simulation.history --run-seed 20261101 --output history-run-1
```

The run seed has no default.  Write it down before the first run; every trial seed comes from it.  Use `--areas`, `--calibration-trials`, `--heldout-trials`, and `--mortality-step` to change the run; a smaller step or fewer trials is for tests, never for the real batch.  The report is `history-run-1/report.json`.  It holds the calibration table for each area, the held-out medians with the 10th and 90th percentiles, the extinct share, the verdict for the main run, and the five statements that the report must make.

## Not done

- The held-out batch has not been run.  A pass would be weak evidence:  three counts are all we hold.
- A run anchored to the occupied area of 264 to 282 km2 (Anastasiya's suggestion of 2026-10-24) is not in the default areas; `--areas` accepts it once Valerie decides.
- The code uses the simulator as it stands (settlement retries every month, current patch first).  The sensitivity rules for retries need an option in the simulator first.
