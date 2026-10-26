# Evaluator code checks (PROPOSED)

Written 2026-10-24 by Valerie with Claude Code.  The code is `validators/results_checks.py`; its tests are `tests/test_results_checks.py`.  Status:  **TESTED ONLY**.  The checks exist as code and a named test runs each one, but no harness calls them yet, so nothing is enforced at runtime.  Nothing here is agreed until Anastasiya says yes.

## What they are for

`docs/agent-handoffs.md` says that JSON Schema cannot establish the relationships inside a results file, and that they "must become runtime checks when the simulation is built."  These are those checks.  The Evaluator agent calls them as a tool and reports what they return; a prompt asks, and this code guarantees.  They read only the input, the results, and the research CSV, and they do not import the simulator, so the Evaluator does not trust the Developer's code.

## The checks

| Name (issue code) | A failure looks like |
|---|---|
| `input_schema`, `results_schema` | a file does not match its schema (the later checks then do not run) |
| `run_identity` | results carry another run ID or seed, or a changed configuration |
| `provenance` | a `simulation` run carries all-zero placeholder hashes |
| `file_hashes` | results and input disagree on the hashes, or a research file changed on disk (skipped on disk for `sample` data) |
| `history_months` | a month is missing or repeated, or month 0 reports births, deaths, or movements |
| `population_accounting` | females plus males is not the population, or population is not last month plus births minus deaths |
| `animal_records` | duplicate animal ID, an unknown patch, or a male or dead animal marked as settled |
| `territory_capacity` | a patch holds more territories than floor(area / female home range) |
| `final_counts` | the last month does not match the living final animals, a created animal is missing, or the dead do not match the deaths |
| `birth_timing_and_food` | births outside March, or births with food below the spring threshold |
| `persistence_recomputed` | `persisted` differs from the value that the final animals give |

## The decision rule

`build_evaluation` returns an `evaluation.json` that matches the schema:  `pass` when every check passes, `revise` when any fails in rounds 0 to 2, and `stop` when any still fails in round 3.  Every issue carries a code, a message, and a requested change.  `historical_validation` stays `not_assessed`.

## How to run it

```bash
python -m validators.results_checks --input input.json --results results.json --output evaluation.json
```

The exit code is 0 for `pass`, 1 for `revise` or `stop`, and 2 for a file that cannot be read or an existing output file.

## What they do not do

- They do not judge the biology or the parameter values.
- They do not replay the run.  The eval plan's bar "the same seed reproduces identical results in 3 of 3 reruns" needs the harness to run the simulator again.
- They do not check the quality of the Researcher's table; the parameter validator and the audit do that.
- They do not call a model.  The Evaluator's judgment about whether the conclusions follow from the results stays a prompt.
