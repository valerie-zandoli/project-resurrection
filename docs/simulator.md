# Synthetic lynx simulator — first preview

This is the numerical model, not a runtime agent workflow. It makes no API calls,
uses no credentials, and performs no historical calibration. Individual lynx are
modeled; rabbit density is constant per run. No disease shock is included.

It follows the agreed survival, food, territory, male-movement, mixed-age, and
persistence rules. The still-proposed conventions from `model-conventions.md`
are explicit: survival → aging → female settlement → male movement → births →
recording; uniform integer litter sizes from the table's low/high bounds; and
monthly settlement attempts in seeded random order, current patch then other
patch. The required `--preview` flag acknowledges those unresolved conventions.
Their use in code or tests is not scientific approval.

## Conventions in the code that the plan did not spell out

These are written here so that nobody has to read the code to learn them.  Each is a convention to agree, not a measured fact.

- **Male crossing starts at the breeding minimum age.**  Only males aged 36 months or more (`breeding_age_min`) can cross to the other patch, with the agreed probability of 0.10 a month.  Younger males stay in their patch.
- **A settled female keeps her territory until she dies,** even after she passes the maximum breeding age (108 months).  An old female can therefore hold a slot that a young female is waiting for, which changes when vacancies open and how fast the population can grow.

## Try after reviewing the model code

Use the repository Python 3.12 environment and install `requirements.txt` plus
`requirements-dev.txt`. From the repository root:

```bash
python -m simulation --preview --months 12 --seed 42 --food 4.6 --area 50 --output /tmp/lynx-preview-42
```

Use a new output directory each time. The default is 20 synthetic animals,
10 females/10 males split equally across patches, uniformly sampled whole-month
ages 36–96. `--months 120` configures the longer synthetic experiment. This first
milestone does not run the 100/500-trial grid or final experiments automatically.

Outputs are `input.json`, schema-valid `results.json`, `summary.json`, and
`history.csv`. The summary includes persistence, final population, extinction
month (`null` if not extinct), and births in the final 12 months. All outputs are
synthetic exploratory results, never observed population history. The summary's
historical-validation status stays `not_assessed`.

The default input computes actual research-file hashes. `--input path.json`
instead consumes an existing version 2 input and checks its hashes; CLI seed,
month, food, and area options apply only when generating a default input.
Do not pass sample all-zero hashes as real provenance.

Input/config version 2.0 records `age_months_min/max`, the model convention label,
male crossing probability, and sensitivity overrides. Results use version 3.0
with required `settled` and the new embedded config; evaluation stays version 1.0.
The eight-column research CSV is unchanged; confidence-column migration is
separate work.

## Checks applied by this local entry point

The entry point validates input schema, finite config numbers, research CSVs,
source references, units, parameter domains, file hashes, distinct patch IDs,
age bounds, equal allocation, and feasible starting capacity before running.
Each month checks population accounting and territory capacity. Death releases
territories, and dead animals retain their last age/patch with `settled=false`.
The model computes persistence using living breeding-age male/female pairs in
one patch with the female settled; food is excluded. Output schema and current
research hashes are checked before writing results.

Month 0 is initialization in `start_month`; transition 1 ends in the next calendar
month. With January initialization, March births are recorded at elapsed month 2.
Newborns are age 0 at birth and face their first survival risk next month.

`random.Random(seed)` is local to each run. Replays require the same Python
version, configuration, parameter files, and code. The future multi-trial runner
must define trial-seed derivation (the proposal in `model-conventions.md`, section 4:
each trial's seed comes from the run seed, the cell name, and the trial number by one
documented rule); no outcome-based reruns or failed-trial removal are implemented
here. Errors stop the single run without retry.  Replays are checked on Python 3.12
only; a different Python version can change the random stream, so the version is
part of what a replay needs.

## Evidence and remaining work

Unit tests exercise these controls; no running multi-agent harness applies them
yet. **TESTED ONLY** remains the status of that integration. This code is not
an execution sandbox. Live generated-code execution still follows the isolation
plan and human-review requirement in `execution-sandbox.md`.

**Contract freeze (proposed).**  The input, results, and evaluation schemas changed twice in two days (results went from 2.0 to 3.0).  Before the first final run (100 pilot and 500 final trials per cell), both owners freeze them.  After the freeze, a change needs a version bump and both owners' agreement, so the Evaluator never checks against a moving schema.

Next work: agree the conventions; independent Evaluator checks; repeated-trial
aggregation/uncertainty; sensitivity orchestration; graphs; and a separate
historical initializer/test. Capacity-limited sensitivity settings that cannot
hold all starting females are rejected rather than silently dropping animals
or changing the agreed starting settlement.
