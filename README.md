# Project Resurrection
Cycle 3 multi-agent system, Pursuit L2

Single-species survival modeling for the Iberian lynx and its prey, the European rabbit.  Three agents (Researcher, Simulation Developer, Evaluator) estimate how food availability and habitat quality affect whether the population persists.  The project rules for coding tools are in `AGENTS.md`.

The [project PRD](docs/prd.md) records the agreed scope, acceptance criteria,
and pending decisions, synchronized from all four Google PRD project tabs.

## What the code does

This section describes the program code on `develop`, checked on 27 November 2026.  Parts of [the architecture notes](docs/architecture.md) describe a design that goes further than the code.  `main` does not yet include the limited repair step described below.

### The three AI roles

- **Researcher:**  reads the existing parameter table, source list, and evidence file.  The case fails if it skips one.  Its short report goes to the Developer as advice.  Code grades its list of low-confidence values and recorded conflicts, and that grade does not change the verdict.  It does not create or change the tables during a run.
- **Simulation Developer:**  runs the fixed simulator.  It does not write or run generated code.  On a revision, the only permitted repair recomputes the saved persistence flag, and only when that is the sole issue.  Any other issue stops the case with `no_progress` for human review.
- **Evaluator:**  calls a tool that runs 2 file-format checks and 10 result checks.  Code decides pass, revise, or stop.  The AI's text is not the verdict, and the Evaluator does not review the program code.  If a file fails its format check, the other checks are skipped.

### Handoffs

Ordinary Python code, called the harness, runs each step and saves the records in a folder for each round.

| Record | What it holds |
|---|---|
| `input.json` | Created by the harness, not the Researcher.  Run settings, including the run ID and random seed, plus the paths and content hashes of the parameter table and source list.  It has no task field and no confidence field.  Confidence labels are in the separate evidence file. |
| `results.json` | The simulator's output:  run ID, seed, revision round, a copy of the run settings, monthly history, final animals, whether the population persisted, assumptions, and whether the data are a sample or a simulation. |
| `evaluation.json` | The checking tool's output:  pass, revise, or stop;  the round number;  the content hashes;  each check;  and a code, message, and requested change for each issue.  `historical_validation` is always `not_assessed`.  The history test writes a separate report. |

There are at most three revision rounds after the first try.  Errors and detected hash mismatches end the case without a retry.  The offline harness (`python -m harness`) uses no AI model;  on a revise verdict it reruns the fixed simulator, up to the same limit.

### Shared state

Before the simulation, the harness makes a read-only copy of the parameter table, the source list, and the evidence file if present, records their content hashes, and validates the copies.  It checks the copies for changes at the start of each round and after the Developer step.  For simulation output, the result checks also compare the parameter table and source list with their hashes.  No AI role has a tool that writes these files.  That only the Researcher changes the source files is a team rule, which this code does not enforce.

### Running it

The commands are under [Running the project](#running-the-project).  The default three-role rehearsal is scripted and calls no AI model.  The [live workflow](docs/live-workflow.md) makes paid requests with a personal key.

### Out of scope for the minimum version

As listed in [the project PRD](docs/prd.md):  individual rabbits, viruses, disease shocks, genetics, detailed maps, a polished dashboard, deployment, and commercial delivery.  Individual lynx are modeled, and rabbit density is a fixed food input in each run.  Results are not broad scientific validation or conservation advice.

## Setup

The [synthetic simulator preview](docs/simulator.md), offline harness, scripted
three-role preview, and opt-in [live workflow](docs/live-workflow.md) are implemented.
The saved live examples are integration evidence, not scientific validation.

Use Python 3.12.  The Mac default `python3` is 3.9, which we do not use.  `python3.12 --version` shows whether 3.12 is installed.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

Copy `.env.example` to `.env` and paste your personal key from LaNice's one-time link.  Never share the key, screenshot it, or commit it.

`python -m pytest` runs the whole test suite without a key. Runtime depends on the environment. Never commit keys or `.env`; this repository is public.

## Running the project

Run every command from the repository root, with the virtual environment active.  Each command that writes files needs a new output folder and never overwrites an old one.

**On `develop` today**

| What | Command | Needs a key |
|---|---|---|
| Check the parameter and source tables | `python -m validators.parameters data/parameters/iberian_lynx_baseline.csv data/parameters/sources.csv` | no |
| Offline harness, one case from research files to a verdict ([details](docs/harness-skeleton.md)) | `python -m harness --preview --seed 7 --months 36 --output case-1` | no |
| Scripted three-role rehearsal ([details](docs/three-role-preview.md)) | `python -m harness.three_role_preview --preview --seed 7 --months 12 --output roles-1` | no |
| Run one synthetic simulator preview ([details](docs/simulator.md)) | `python -m simulation --preview --months 12 --seed 42 --food 4.6 --area 50 --output /tmp/lynx-preview-42` | no |
| Test the key in `.env` with one small call | `python scripts/check_key.py` | yes |
| Trial batches by food level and area ([details](docs/simulator-batches.md)) | `python -m simulation.experiments --preview --stage pilot --seed 20261025 --trials 100 --months 120 --output batch-1` | no |
| Evaluator checks on one results file ([details](docs/evaluator-checks.md)) | `python -m validators.results_checks --input input.json --results results.json --output evaluation.json` | no |
| Report table and figure from a batch file ([details](docs/report-skeleton.md)) | `python -m report.figures batch-1/batch.json --table table1.md --figure figure1.svg` | no |
| History test (**run it once, after the freeze**:  it prints the 2011 count and always runs the final evidence gate; see `docs/history-test-code.md`) | `python -m simulation.history --run-seed 20261101 --output history-run-1` | no |

The history test and the batches are not results until a run with a recorded seed says so; the preview batches use a synthetic start and are not a history test. The default harness and scripted rehearsal call no model. Real provider calls require the explicit live command in the [live-workflow guide](docs/live-workflow.md); see that guide for the saved runs and their limits.
