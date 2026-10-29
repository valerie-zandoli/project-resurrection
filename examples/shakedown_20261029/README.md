# Shake-down of 2026-10-29:  saved runs for the fallback bundle

Saved by Valerie with Claude Code from the shake-down of Thursday 2026-10-29, as `docs/demo-plan.md` ("The fallback") and `docs/live-pass-runbook.md` (step 9) ask.  The code was `develop` at 60e2ef6.  These are a rehearsal.  They are **not** the final recorded runs, which come after the freeze, and they are integration runs on synthetic data, not scientific results.  Historical validation is not assessed.

## What is here

| Folder | What it is | Key needed |
|---|---|---|
| `offline-case/` | One offline case (`python -m harness --preview --seed 7 --months 36`):  status `pass`, 0 issues, 1 attempt | no |
| `hand-back/` | The scripted hand-back example (`python -m harness.handback_example`):  stops on its unresolved gap, as designed; no model is called | no |
| `live-claude/` | The live case that passed (attempt 4 below):  6 of 12 Claude calls, all 12 code checks, the evidence read check passed | yes |
| `live-claude-failed-attempts/` | The `live-summary.md` of the three failed attempts | yes |

Each folder holds `case.json` (the status and the reasons), `trace.jsonl` (one numbered line per harness step), and the run's `round_0` files where the run has them.  The research snapshot is left out:  its two files and the evidence file are in git at 60e2ef6, and their hashes are in `case.json`.  `live-claude/roles.jsonl` holds the full prompts, the tool results, and the model's replies (research text and replies only; no key, and no local path).  Each trace was read line by line before it was committed.

## The four live attempts, and the override

| Attempt | Finished (ET) | Result | Why |
|---|---|---|---|
| 1 | 14:18:12 | failed after 2 of 12 calls | The Researcher's second reply hit the reply limit |
| 2 | 14:21:29 | failed after 2 of 12 calls | The same |
| 3 | 14:29:49 | failed after 2 of 12 calls | The same; a watching script showed `finish_reason: length`, no visible text, exactly 1,200 completion tokens |
| 4 | 14:34:51 | **pass**, 6 of 12 calls | The same watching script, with the reply limit raised to 4,000 for that run only |

**The override.**  The committed code at 60e2ef6 has `MAX_TOKENS = 1200` in `harness/litellm_provider.py`.  The limit counts the model's hidden reasoning as well as its visible text, and the model used all 1,200 tokens before any visible word.  Attempt 4 ran the same code with the limit set to 4,000 in memory, by a watching script outside the repository.  The largest reply in attempt 4 used 1,003 tokens (493 of reasoning, 510 visible).  `live-claude/live.json` records the hash of the committed file, which has the limit 1,200, so it does **not** describe the limit that attempt 4 used.  Pull request #136 makes 4,000 the committed limit, and the final live pass must be run on the code that has it.

## What this shows and does not show

It shows that the path from the research files through three Claude roles to a code-checked verdict works once, with a raised limit.  It does not show that the model behaves this way every time, that any parameter value is right, or anything about history.  The Researcher inspects existing tables; full scientific evidence review is not demonstrated.
