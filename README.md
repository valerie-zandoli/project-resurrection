# Project Resurrection
Cycle 3 multi-agent system, Pursuit L2

Single-species survival modeling for the Iberian lynx and its prey, the European rabbit.  Three agents (Researcher, Simulation Developer, Evaluator) estimate how food availability and habitat quality affect whether the population persists.  The project rules for coding tools are in `AGENTS.md`.

The [project PRD](docs/prd.md) records the agreed scope, acceptance criteria,
and pending decisions, synchronized from all four Google PRD project tabs.

## Setup

The [synthetic simulator preview](docs/simulator.md) runs the first seeded
numerical milestone; the live multi-agent harness is still pending.

Use Python 3.12.  The Mac default `python3` is 3.9, which we do not use.  `python3.12 --version` shows whether 3.12 is installed.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

Copy `.env.example` to `.env` and paste your personal key from LaNice's one-time link.  Never share the key, screenshot it, or commit it.

`python -m pytest` runs the whole test suite in a few seconds and needs no key.  Never commit keys or `.env`; this repository is public.

## Running the project

Run every command from the repository root, with the virtual environment active.  Each command that writes files needs a new output folder and never overwrites an old one.

**On `develop` today**

| What | Command | Needs a key |
|---|---|---|
| Check the parameter and source tables | `python -m validators.parameters data/parameters/iberian_lynx_baseline.csv data/parameters/sources.csv` | no |
| Run one synthetic simulator preview ([details](docs/simulator.md)) | `python -m simulation --preview --months 12 --seed 42 --food 4.6 --area 50 --output /tmp/lynx-preview-42` | no |
| Test the key in `.env` with one small call | `python scripts/check_key.py` | yes |

**In open pull requests (these work only after the pull request merges)**

| What | Command | Pull request |
|---|---|---|
| Trial batches by food level and area | `python -m simulation.experiments --preview --seed 20261025 --trials 100 --months 120 --output batch-1` | #48 |
| History test | `python -m simulation.history --run-seed 20261101 --output history-run-1` (see `docs/history-test-code.md`) | #50 |
| Evaluator checks on one results file | `python -m validators.results_checks --input input.json --results results.json --output evaluation.json` | #51 |
| Offline harness, one case from research files to a verdict | `python -m harness --preview --seed 7 --months 36 --output case-1` (see `docs/harness-skeleton.md`) | #56 |
| Report table and figure from a batch file | `python -m report.figures batch-1/batch.json --table table1.md --figure figure1.svg` | #63 |

The history test and the batches are not results until a run with a recorded seed says so; the preview batches use a synthetic start and are not a history test.  The harness runs offline and calls no model, so no agent runs through it yet.
