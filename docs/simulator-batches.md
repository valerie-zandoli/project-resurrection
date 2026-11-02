# Repeated synthetic previews

After reviewing the model, use Python 3.12 from the repository root:

```bash
python -m simulation.experiments --preview --stage pilot --seed 42 --trials 100 --months 120 --output /tmp/lynx-batch-42
```

This runs six cells: food densities 1, 4.6, and 55 rabbits per hectare, each
with two 50 km² patches or two 100 km² patches. Each trial uses the existing
20-animal synthetic initialization and validates its inputs and outputs through
the existing simulator. No research values, biological rules, or handoff schemas
change. See [the single-run simulator](simulator.md).

This entry point requires `--preview`. Monthly event order, settlement conventions,
litter sampling, and the aggregation proposal remain provisional. Even 100 or
500 trials here are previews, not approved pilot/final experiments. This runner
does not implement the proposed human source audit, final-run evidence gate,
independent evaluation, sensitivity runs, history calibration, or live agents.
Historical validation stays `not_assessed`. Do not mix separate batches.

## Replaying a trial

Trial numbers start at zero. The seed is the first eight bytes of SHA-256,
interpreted as an unsigned big-endian integer, over ASCII compact JSON:
`["lynx-preview-batch-v1",batch_seed,cell_name,trial_number]`. For example, the
medium-food/small-area cell is `food-4.6_area-50`. Python's randomized `hash()` is
never used. Seeds are independent of execution order; no outcome changes them.
This derivation is an implementation proposal for review.

Each trial directory contains `input.json`, `results.json`, and `summary.json`.
Replay its exact input with `python -m simulation --preview --input INPUT_PATH
--output NEW_DIRECTORY` (on one command line). Use the same Python version, model,
schemas, and research files. `batch.json` records Python version, code/schema
hashes, the seed rule, every attempted trial, and the evidence-gate `stage` that
the command ran at (`pilot` or `final`; `null` when `run_batch` is called without
the command). A pilot only warns about unchecked evidence, so only a batch whose
`stage` is `final` counts as the final grid (`scripts/check_fallback.py`). Research hashes are in the
saved inputs and are captured before the batch; an edit during execution stops
the batch. Batch identity also includes configuration, research/code hashes,
Python version, and planned trial count, so changed inputs get different run IDs.

## Summaries and failures

A completed cell reports persistence share and a two-sided 95% Wilson interval,
median final population, its 10th/90th percentiles, extinction share, and median
extinction month among extinct trials. Quantiles linearly interpolate sorted
values at `(n - 1) * fraction`. No extinction means a null median extinction time.
These intervals describe variation under the model; they do not include all
uncertainty in the evidence or assumptions.

Each attempt is recorded as running before execution, then completed or failed.
A failure stops the whole batch without retry. The failed cell retains its
planned count and all attempts, has null statistics, and is marked incomplete;
later cells remain pending. Earlier complete cells retain their summaries.
A killed process leaves a running batch/attempt, which must never be treated as
complete. Existing output directories are refused; there is no resume or silent
overwrite. The command exits unsuccessfully for an incomplete batch.
