# History test: what is compared, how, and when (PROPOSED)

Drafted 2026-10-22 by Valerie with Claude Code.  Valerie owns the history test.  Everything here is a proposal until Anastasiya agrees, except the two tolerances, which Valerie accepted on 2026-10-22 and Anastasiya has not yet confirmed.  The area decision of 2026-10-24 is also Valerie's and awaits Anastasiya.  Items marked (assumption) have no support in the data we hold.

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

## Decision:  the usable area of the history run (2026-10-24)

Valerie chose the recommendation below on 2026-10-24.  Anastasiya has not yet confirmed it.

- **Main run:**  750 km2 in total, labeled in every report as an assumption.  The usable area of the Andujar-Cardena nucleus alone is not sourced.  The nearest figure found is the Sierra de Andujar protected area, 74,774 hectares or about 750 km2 (https://web.ujaen.es/revista/jja/pdf/0004-01/jja-0004-01-12-diputacion.pdf).  A protected area is not the same as usable lynx habitat, so the figure is a stand-in.
- **Sensitivity runs:**  500 km2 and 1,000 km2.  The 1,000 km2 figure matches two rough ranges for the wider area:  Sierra Morena near 1,000 km2 (a 2020 news report, https://theolivepress.es/spain-news/2020/05/11/once-endangered-iberian-lynx-now-thriving-in-spains-andalucia/) and the Andalusian lynx range of 1,019 km2 in 2011 (the EU LIFE project page, project LIFE10-NAT-ES-000570).  Valerie has read none of these three sources in full.
- **Capacity:**  the area sets the number of female territories:  about 75 at 750 km2 (area divided by the 10 km2 home range), 50 at 500 km2, and 100 at 1,000 km2.  All three exceed the 44 adult females counted in 2010, but that count still does not fix a minimum area, because living females can stay unsettled.
- **What does not change:**  the tolerances, the calibration steps, the trial count, and the held-out rule below.  Calibrate at each of the three areas.  The pass or fail verdict uses the 750 km2 run only; that rule is fixed here, before any run.  The runs at 500 and 1,000 km2 are reported beside it, with the calibrated mortality at each area, to show how far the assumption moves the result.  They never replace it.

## Calibration

- Change one parameter only:  post-dispersal annual mortality (`annual_mortality_rate_all_causes`), searched from 0.10 to 0.50.  Every other parameter stays at its baseline.
- Use 2002 to 2010 only.  Choose the mortality whose median growth is closest to 1.17.
- Then run one frozen held-out batch:  the same number of trials as the final runs (500), with a seed rule fixed before the run (each trial's seed comes from the run seed, the word "heldout", and the trial number).  Run the predefined ensemble through month 108.  Mortality and every other setting stay frozen after calibration.
- The pass criterion is the median over the trials of that batch.  Report pass or fail against the tolerance.  Do not re-calibrate, and do not retune anything, after seeing the 2011 result.
- A hand check with the published rates puts growth near 0.99 at mortality 0.37 and near 1.16 at 0.20.  This is arithmetic and not a simulation result.

## The report must say

The three-anchor limit; that Donana parameters are applied to Andujar-Cardena (a transfer assumption); the starting-population assumptions; the census-date assumption; the usable area as an assumption, with the calibrated mortality and results at 500 and 1,000 km2; the trial count; the median and the 10th to 90th percentile of growth and of the 2011 count; and the share of trials that went extinct.
