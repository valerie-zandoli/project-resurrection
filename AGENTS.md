# Project Resurrection: rules for coding tools

Claude Code and Codex both read these rules (`CLAUDE.md` imports this file).  Change the rules here, not in a tool-specific file.

## Project

Single-species survival modeling for the Iberian lynx and its prey, the European rabbit.  Research question:  how do food availability and habitat quality affect the likelihood that the population persists over a fixed period?

## Architecture (agreed)

Researcher, then Simulation Developer, then Evaluator.  The Evaluator returns problems to the Simulation Developer for revision.  Code manages every handoff; a separate coordinator agent is optional.

- Researcher:  supplies a sourced parameter table and assumptions.
- Simulation Developer:  builds the model and runs the experiments.
- Evaluator:  checks the implementation and the conclusions.
- The simulated lynx and rabbits live inside the model.  They are not the AI agents.

## Ownership

- Valerie (Person 1):  Researcher, Evaluator, baseline history test.
- Anastasiya (Person 2):  Simulation Developer, parameter table validator.
- Together:  the parameter table format (written first), the harness, the presentation.

Also agreed:

- The harness is pair-programmed from 16:00 to 18:00 ET, and the revision loop stops after 3 rounds and reports to both of us.
- Each of us writes the code check for the other's output.  Anastasiya writes the parameter table validator (every parameter has a source and a range).  Valerie writes the baseline history test (the model reproduces the lynx's known population history within a tolerance set before any run).

## Stretch goal

Run the black-footed ferret and prairie dog with the same model template.  It passes if the second pair needs no change to the model code, only a new sourced parameter table, and its report passes the same checks.  Run it only if the lynx build leaves time.

## Git workflow (from LaNice, Task 10, 2026-10-21)

- `main` is the stable version.  It changes only by a pull request from `develop`, after `develop` is checked.
- `develop` is where finished work lands first.  It changes only by pull requests from task branches.
- Each task gets one branch, started from `develop` and named for what it does (for example `data/census-2024-2025`).  Never push straight to `main` or `develop`.
- Pull `develop` before you start and again right before you push.  Push your task branch often.
- One pull request, one thing:  if the description needs the word "and", split it.  Keep each one small enough to read in a few minutes.
- Keep AI changes small:  ask for one task, name the files the AI may change, read `git diff` before every commit, and undo anything you did not ask for.  Commit after each small win.
- To fix a conflict, pull `develop` into your task branch first, resolve it there, remove every marker, run `python -m pytest`, then commit.
- `main` and `develop` both need a pull request, one approval, and a passing `tests` check.  Delete a task branch after it merges.

## Working rules

- Ask "push or wait?" before changing a shared file.
- Work in separate files, and follow the Git workflow above.
- Write the interfaces between the agents before anyone builds.
- A prompt asks; code guarantees.  Any rule that must always hold goes in code with a test, and the design notes which of the two enforces it.
- Never commit keys, `.env`, or private data.  This repository is public.

## Working with LLM tools (added 2026-10-24, from Anastasiya's suggestions)

- Before implementation work, read `.agents/skills/project-resurrection/SKILL.md`.  It applies to Codex and to Claude Code alike.
- LaNice's learning slides are teaching material.  Any architecture in them is only an example.  Our architecture is already established (see above and `docs/architecture.md`), so when a slide differs, follow ours.
- Review code carefully for correctness and for whether it works, then stop.  Do not chase perfection, and do not loop between Claude Code and Codex reviewing each other's reviews.  Flag any remaining non-blocking concern in the pull request, and the owners decide.

## Setup

- Python version:  3.12.  The Mac default `python3` is 3.9, which we do not use.
- Test command:  `python -m pytest`, run inside the virtual environment.  The setup steps are in the README.
