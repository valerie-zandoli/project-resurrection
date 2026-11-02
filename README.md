# Project Resurrection
Cycle 3 multi-agent system, Pursuit L2

Single-species survival modeling for the Iberian lynx and its prey, the European rabbit.  Three agents (Researcher, Simulation Developer, Evaluator) estimate how food availability and habitat quality affect whether the population persists.  The project rules for coding tools are in `AGENTS.md`.

The [project PRD](docs/prd.md) records the agreed scope, acceptance criteria,
and pending decisions, synchronized from all four Google PRD project tabs.

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
