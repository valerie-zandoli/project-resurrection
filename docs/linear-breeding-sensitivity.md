# Gradual breeding sensitivity

Valerie accepted this comparison in Slack on 2026-10-26 at 12:44 ET. It is an
assumed alternative to the baseline, not a measured food-response curve.

`spring_threshold` remains the default: no breeding below the spring cutoff;
eligible females breed with the parameter table's annual probability at or above
it. The cutoff itself is an assumption. Default seeded numerical outputs remain
unchanged.

`linear_food_sensitivity` multiplies the table's annual breeding probability by
`min(food / 4.6, 1)`. With today's table this gives 0% at zero rabbits per hectare,
18.1% at 1, 41.65% at 2.3, and 83.3% at 4.6 or higher. Breeding still happens only
in March, for eligible territorial females with an eligible male in their patch.
The probability is applied once per eligible female in that breeding season.
Mortality, litter size, settlement, and endpoint persistence use their existing rules.

Run one preview:

```sh
python -m simulation --preview --seed 7 --months 12 --food 2.3 --breeding-rule linear_food_sensitivity --output /tmp/lynx-linear-7
```

Run separate synthetic pilot batches with matched trial seeds:

```sh
python -m simulation.experiments --preview --seed 7 --trials 100 --months 120 --output /tmp/lynx-step-batch
python -m simulation.experiments --preview --seed 7 --trials 100 --months 120 --breeding-rule linear_food_sensitivity --output /tmp/lynx-linear-batch
```

Use new folders; outputs are never overwritten. The batch manifest names the
breeding rule, and each saved input/results pair carries the configuration.
Changing the rule creates a different batch identity while preserving the trial
seed schedule. Do not combine this linear comparison with a changed spring
threshold: it is fixed at 4.6 for this comparison, and other threshold overrides
are rejected. Settlement alternatives may be selected independently.

Inputs selecting the new option use schema 2.2, with explicit `breeding_rule` and
`settlement_rule`; their results use schema 3.2. Legacy inputs 2.0/2.1 continue to
run the threshold rule and keep the existing normalization/results behavior.
Supplying the new field under an old version is rejected rather than silently
changing its meaning. Evaluation format remains 1.0.

The independent birth check permits below-cutoff births only under the linear
option, continues to reject births at zero food or outside March, and does not
claim a statistical check of breeding probabilities. Tests check the numerical
chance, cap, seasonal/pair requirements, reproducibility, recorded configuration,
and preservation of pre-change default results.

The historical calibration and held-out history test are unchanged. Do not use
this alternative to tune the historical test. These commands produce synthetic
previews; historical validation remains `not_assessed`. The examples are commands,
not claims that the 100-trial pilot or final experiments have been run.
