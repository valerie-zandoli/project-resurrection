# History test: what is compared, how, and when (PROPOSED)

Drafted 2026-10-22 by Valerie with Claude Code. Valerie owns the history test. The 2011 target and area plan below were agreed by Valerie and Anastasiya on 2026-10-25; other test choices remain proposals unless the text records agreement. The area and home-range values are modeling assumptions, not measurements of usable habitat.

## The question

Does the model, run with the Donana parameters, grow a population from the 2002 Andujar-Cardena count at about the rate the later counts show, and land near the 2011 count that it never saw? Three counts are all we have (`data/history/counts.csv`), so a pass is weak evidence and the report must say so.

## The data

- 2002: 53 individuals, of which 25 adults.
- 2010: 190 individuals, of which 44 adult females.
- 2011: 202 individuals in the issuer's [official 2011 census series](https://www.iberlince.eu/files/images/docs/3_informeslife/informe_censo_2011.pdf) (held out), also reported in the issuer's [2016 census report](https://www.iberlince.eu/files/images/docs/3_informeslife/informe_censo_2016.pdf). The Cat Specialist Group page gives 214; retain 214 as a comparison value, not as the verdict target. The reason for the discrepancy is unknown.
- Observed growth: (190 / 53) ^ (1 / 8) = 1.173 per year from 2002 to 2010; (202 / 53) ^ (1 / 9) = 1.160 per year to 2011, using the official series.

## What is compared

- **Quantity:** total living animals of every age, counted at the same calendar month each year. The census date is not known to us (assumption: the end of the year; confirm it before the first run).
- **Growth,** per trial: (N at month 96 / N at month 0) ^ (1 / 8), where month 0 is the 2002 count and month 96 the 2010 count.
- **Held-out count,** per trial: N at month 108, the 2011 count.
- **Summary:** the median of each quantity over all trials of one setting.

## The tolerances (set before any run, never changed after the 2011 result)

- Median growth within 0.05 of 1.17, that is 1.12 to 1.22.
- Median 2011 count within 10% of 202, that is 181.8 to 222.2. Report the 214 comparison beside the verdict; it does not affect pass or fail.

## The starting population (assumption, except the two counts)

- 53 animals: 25 adults and 28 non-adults, from the counts.
- Adults: whole-month ages drawn uniformly from 36 to 108 months (`breeding_age_min` to `breeding_age_max`); sex 1 : 1 (assumption).
- Non-adults: whole-month ages drawn uniformly from 0 to 35 months; the cub sex ratio of the table (1.03 females per male).
- All draws use the run seed. The synthetic 20-lynx start is a separate experiment and is never reused here.

## Agreed area plan: primary boundary and occupied-area comparisons (2026-10-25)

Valerie clarified that 750 km2 is a stand-in for the boundary of the Sierra de Andujar Natural Park (about 749 km2), not a measurement of usable lynx habitat. The usable area of the Andujar-Cardena nucleus itself is not sourced. This plan keeps 750 km2 as the primary model-boundary assumption and compares it with the historical occupied area using two home-range assumptions. The team agreed to drop the 500 and 1,000 km2 comparison runs.

- **Primary run:** 750 km2 as the model boundary, with the existing 10 km2 female home-range assumption. Label 750 km2 as a park-boundary stand-in, not measured usable habitat.
- **Comparison runs:** 264 km2 with a 6.1 km2 home-range assumption, and 264 km2 with a 10 km2 home-range assumption. Valerie reported that her exploratory runs at 500, 750, and 1,000 km2 all calibrated to the same mortality (0.16), so those comparisons showed little. She accepted the 264 km2 comparisons instead.
- **Evidence and limits:** Valerie reported census-chart figures of 264 km2 occupied in 2010 and 282 km2 in 2011, with 43 and 51 territorial females, respectively. The 264 km2 comparison uses the 2010 figure. Cite the issuer's [2010 census report (`informe_censo_2010`)](https://www.iberlince.eu/files/images/docs/3_informeslife/informe_censo_2010%281%29.pdf) alongside the [WWF source chart](https://awsassets.wwf.es/downloads/lince_online_newsletter_2_mayl14_def.pdf); occupied area is not automatically the same as usable habitat.
- **Territory capacity:** calculate whole territories separately within each of the two equal patches, rounding down in each patch, then add the patch capacities. The 750 km2 run has two 375 km2 patches, so it allows 2 x floor(375 / 10) = 74 female territories. Each 264 km2 comparison has two 132 km2 patches, allowing 2 x floor(132 / 6.1) = 42 territories or 2 x floor(132 / 10) = 26. These are model capacity estimates, not observed territory counts. The 6.1 km2 value is a sensitivity assumption for comparison, not a claim that all females have that measured home range.
- **Interpretation:** calibrate and report the primary and comparison settings using the same procedure. The pass or fail verdict uses the 750 km2 primary run only. Report the comparison results and calibrated mortality beside it so readers can see how the boundary and home-range assumptions affect the result; comparison runs do not replace the primary verdict.

The tolerances, calibration steps, trial count, and held-out rule below do not change.

## Calibration

- Change one parameter only: post-dispersal annual mortality (`annual_mortality_rate_all_causes`), searched from 0.10 to 0.50. Every other parameter stays at its baseline.
- Use 2002 to 2010 only. Choose the mortality whose median growth is closest to 1.17.
- Then run one frozen held-out batch: the same number of trials as the final runs (500), with a seed rule fixed before the run (each trial's seed comes from the run seed, the word "heldout", and the trial number). Run the predefined ensemble through month 108. Mortality and every other setting stay frozen after calibration.
- The pass criterion is the median over the trials of that batch. Report pass or fail against the tolerance. Do not re-calibrate, and do not retune anything, after seeing the 2011 result.
- A hand check with the published rates puts growth near 0.99 at mortality 0.37 and near 1.16 at 0.20. This is arithmetic and not a simulation result.

## The report must say

The three-anchor limit; that Donana parameters are applied to Andujar-Cardena (a transfer assumption); the starting-population assumptions; the census-date assumption; the 750 km2 primary boundary as an assumption; the 264 km2 comparison results at both home-range assumptions and the calibrated mortality for each; the trial count; the median and the 10th to 90th percentile of growth and of the 2011 count; and the share of trials that went extinct.
