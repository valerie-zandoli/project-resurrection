# History test: what is compared, how, and when (PROPOSED)

Drafted 2026-10-22 by Valerie with Claude Code.  Valerie owns the history test.  Everything here is a proposal until Anastasiya agrees, except the two tolerances, which Valerie accepted on 2026-10-22 and Anastasiya has not yet confirmed.  Items marked (assumption) have no support in the data we hold.

## The question

Does the model, run with the Donana parameters, grow a population from the 2002 Andujar-Cardena count at about the rate the later counts show, and land near the 2011 count that it never saw?  Three counts are all we have (`data/history/counts.csv`), so a pass is weak evidence and the report must say so.

## The data

- 2002:  53 individuals, of which 25 adults.
- 2010:  190 individuals, of which 44 adult females.
- 2011:  214 individuals, of which 90 adults (held out).
- Observed growth:  (190 / 53) ^ (1 / 8) = 1.173 per year from 2002 to 2010;  (214 / 53) ^ (1 / 9) = 1.168 per year to 2011.

## What is compared

- **Quantity:**  total living animals of every age, counted at the same calendar month each year.  The census date is not known to us (assumption:  the end of the year; confirm it before the first run).
- **Growth,** per trial:  (N at month 96 / N at month 0) ^ (1 / 8), where month 0 is the 2002 count and month 96 the 2010 count.
- **Held-out count,** per trial:  N at month 108, the 2011 count.
- **Summary:**  the median of each quantity over all trials of one setting.

## The tolerances (set before any run, never changed after the 2011 result)

- Median growth within 0.05 of 1.17, that is 1.12 to 1.22.
- Median 2011 count within 10% of 214, that is 192.6 to 235.4.

## The starting population (assumption, except the two counts)

- 53 animals:  25 adults and 28 non-adults, from the counts.
- Adults:  whole-month ages drawn uniformly from 36 to 108 months (`breeding_age_min` to `breeding_age_max`); sex 1 : 1 (assumption).
- Non-adults:  whole-month ages drawn uniformly from 0 to 35 months; the cub sex ratio of the table (1.03 females per male).
- All draws use the run seed.  The synthetic 20-lynx start is a separate experiment and is never reused here.

## Open decision:  the usable area of the history run

The usable area sets how many female territories exist (area divided by the 10 km2 home range).  The 2010 count gives 44 adult females, but that count does not show 44 territorial females, because the model lets living females stay unsettled.  So the count does not fix a minimum area.

- If the usable area of the Andujar-Cardena nucleus can be sourced, use it and cite it.
- Otherwise label the chosen area (and so the territory capacity) as an assumption, and calibrate at two or three areas to show how far the area moves the calibrated mortality.
- A small capacity can limit growth and so affect the calibration; it does not by itself make the calibration meaningless.

## Calibration

- Change one parameter only:  post-dispersal annual mortality (`annual_mortality_rate_all_causes`), searched from 0.10 to 0.50.  Every other parameter stays at its baseline.
- Use 2002 to 2010 only.  Choose the mortality whose median growth is closest to 1.17.
- Then run one frozen held-out batch:  the same number of trials as the final runs (500), with a seed rule fixed before the run (each trial's seed comes from the run seed, the word "heldout", and the trial number).  Run the predefined ensemble through month 108.  Mortality and every other setting stay frozen after calibration.
- The pass criterion is the median over the trials of that batch.  Report pass or fail against the tolerance.  Do not re-calibrate, and do not retune anything, after seeing the 2011 result.
- A hand check with the published rates puts growth near 0.99 at mortality 0.37 and near 1.16 at 0.20.  This is arithmetic and not a simulation result.

## The report must say

The three-anchor limit; that Donana parameters are applied to Andujar-Cardena (a transfer assumption); the starting-population assumptions; the census-date assumption; the trial count; the median and the 10th to 90th percentile of growth and of the 2011 count; and the share of trials that went extinct.
