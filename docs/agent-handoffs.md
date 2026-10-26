# Agent handoffs — results version 3.1

For Valerie and Anastasiya to review before simulation integration. JSON Schemas
in `schemas/` define the shapes; matching examples live in `examples/handoffs/`.
These examples are hand-authored fixtures, not generated scientific results.

## Flow

Researcher supplies the existing eight-column parameter CSV and source registry.
Run the parameter validator first. The harness then supplies `input.json` to the
simulation developer. A run produces `results.json`; the evaluator returns
`evaluation.json`. The contracts do not implement AI calls or the harness.
The local numerical preview is described in [simulator.md](simulator.md).

## Input

Input version 2.1 records the agreed mixed-age synthetic start: 10 females and
10 males, five of each sex per patch, with seeded uniform whole-month ages from
`age_months_min` (36) to `age_months_max` (96), inclusive. It replaces the old
single `age_months` field. These are synthetic assumptions, not historical
starting conditions. `habitat_quality` stays 1.0; usable patch area controls
female territory capacity. Rabbits remain a constant density input, with no
disease shock. The sample final states are illustrative, not generated results.

`model_conventions: proposed-2026-10-22` records the pending monthly-order,
litter-sampling, and settlement-choice conventions used by the preview simulator.
It does not mark them agreed. Male crossing probability is explicit in the
configuration. `parameter_overrides` records only the agreed sensitivity axes:
post-dispersal annual mortality 0.10–0.50, female home range 4–30 km², and spring
breeding threshold 3.0–6.0 rabbits/ha. Input and embedded config use version 2.1;
results use version 3.1 to record the settlement rule; evaluation stays version
1.0. Version 2.0 inputs and version 3.0 results remain readable.

`start_month` is the calendar month at elapsed month 0. `duration_months` counts
transitions after initialization. Paths are repository-relative. The proposed
experiment duration is 120 months, but the example uses one month for inspection.
Record the random seed and full configuration in results. Reproduction rules,
food/habitat effects, and any parameter overrides need agreement before runs.

## Agreed persistence and settlement

Agreed by Valerie and Anastasiya on October 22, 2026: persistence requires at
least one living breeding-age female that holds a territory and one living
breeding-age male in the same patch at the endpoint (`duration_months`, 120 in
the main experiment). Use the parameter table's inclusive breeding-age bounds,
converting years to months; baseline bounds are 36–108 months for both sexes.
Food availability is excluded from this endpoint eligibility and affects
reproduction separately. Report births in the final 12 months alongside
persistence so surviving pairs without recent reproduction remain visible.
This endpoint does not establish long-term viability.

The input field `persistence_rule` carries the rule name `settled_breeding_pair_same_patch_at_end`.  It was `breeding_pair_same_patch_at_end` until 2026-10-24, a name that left out the territory.  The name changed inside the unmerged input 2.0 and results 3.0 contracts, so no further version bump was needed; an input file that still has the old name no longer validates.

Every entry in `final_animals` requires a boolean `settled`:

- A living female is `true` after acquiring a free female territory. Starting
  females are `true`: five occupied territories per patch.
- Young females are `false` until dispersal and successful settlement. Unsettled
  females stay alive under the agreed all-cause mortality.
- Males are always `false` because they use no female territory slots. Their
  `settled` value is not an eligibility requirement for persistence.
- A female retains her territory while alive unless an agreed movement rule
  changes it. Death frees the slot and sets `settled` to `false`. Dead animals
  remain in the final list, retaining age and patch at death.

The schema rejects missing/nonboolean `settled` values and rejects `true` for a
male or dead animal. Results schema **3.1** records the settlement rule in its
embedded version 2.1 input contract. It retains support for prior version 3.0
results and embedded version 2.0 configurations; evaluation remains version 1.0.
Old results must not be accepted by silently treating missing `settled` as true
or falling back to the weaker pair-only rule. Regenerate or explicitly migrate
old artifacts from known territory states; do not infer them from sex alone.

The local preview implements settlement transitions, territory-capacity checks,
age eligibility, persistence calculation, and the final-12-month births summary.
These are Developer-side calculations with tests, not independent evaluation.
The future Evaluator must independently recompute `persisted` from final states.
Schema validation alone does not prove these behaviors. Settlement retry order
and cross-patch female movement remain separate open conventions; the preview
uses them provisionally and this implementation does not settle them.

## Results

`history` contains month 0 through `duration_months`, inclusive. Month 0 has zero
births, deaths, and movements. Later event counts cover the preceding monthly
transition. Movement counts animals changing patch at least once that month.
`final_animals` includes every animal created, including dead animals; age and
patch for dead animals are their last state at death. IDs stay unique for a run.
`population`, `females`, and `males` count living animals. Births and deaths must
balance each transition; moves do not change total population.

`data_kind: sample` identifies fixtures; real model runs use `simulation`.
The harness must verify matching run IDs/seeds/configurations, contiguous months,
unique animal and patch IDs, valid patch references, final counts, and persistence
against final animal states. JSON Schema alone does not establish these semantic
relationships. They must become runtime checks when the simulation is built.

## Evaluation and bounded revisions

`pass` means all reported checks passed and no issues remain. `revise` means
issues need developer changes; each issue includes a code, message, and requested
change. `stop` is required if unresolved issues remain at revision round 3.
Round 0 is the initial attempt; rounds 1–3 are revisions. On stop, the harness
must report to both teammates. Those behavioral rules require harness tests;
the schemas constrain round numbers, field shapes, and the link between the status
and its evidence (a `pass` lists no issue and no failed check; a `revise` lists at
least one issue).

This version is for synthetic experiments. `historical_validation: not_assessed`
prevents an example format check from implying a historical fit. Historical
comparison requires a separate agreed initialization, observation definition,
calibration/validation split, and tolerance. Do not reuse the 20-lynx fixture as
historical initialization.

## Content hashes

The inputs name the research files by path, and the Researcher can still edit them. A path alone does not say which version of a file a run used, so a run could be evaluated against a table it never read (a stale-data read).

`input.json` therefore records `parameters_sha256` and `sources_sha256`, the content hashes of the two CSV files it names. A content hash is a short fingerprint of a file's contents. `results.json` carries the same values inside `config`, and `evaluation.json` carries them at the top level. Hashes ignore the CRLF/LF difference so every checkout agrees. The sample fixtures use all-zero placeholders; a real run computes them with `validators/handoff_hashes.py`.

The harness must run two checks, which are code and not a prompt:

- `check_handoff_hashes(input, results, evaluation)` before it accepts results and again before it accepts an evaluation. Any difference rejects the handoff.
- `check_files_current(input, root)` at the start of every revision round. A changed file rejects the round.

If the Researcher changes a CSV on purpose, that is not a revision of the old run. The harness starts a new run from a fresh `input.json` with new hashes and a new run ID.

A hash proves two agents read the same file, not that the file is correct. Checking the table against its sources stays a separate job.

## Check contracts locally

```bash
pip install -r requirements-dev.txt
python -m pytest tests/test_handoffs.py
```

`jsonschema` is a development dependency, so the required `tests` check runs
these tests. A missing `jsonschema` makes them fail; it never skips them.
The Handoff contracts CI workflow still installs `requirements-handoffs.txt`
(the same pin) and runs the full test suite.
