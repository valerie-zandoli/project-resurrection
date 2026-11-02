# Live-pass runbook (PROPOSED)

Written 2026-10-25 by Valerie with Claude Code, for the shake-down live pass on Thu 2026-10-29 (17:30 to 19:30 ET, Valerie alone), the freeze on Fri 2026-10-30 at midday, and the final recorded live pass by Fri 2026-10-30, 18:00 ET (`docs/demo-plan.md`, #54).  Nothing here is agreed until Anastasiya says yes.  Items marked **TO FILL** wait for code that Anastasiya owns (the live provider and the Developer wiring, decision 8); no command for them is invented here.

## What a live pass is

One case, from the research files to `pass`, `stop`, `rejected`, or `failed`, in which a role calls a live model through the harness.  The Developer is the fixed `run_model` tool (decision 4), so the live calls are the Researcher's and the Evaluator's explanations.  The Evaluator's code checks decide `pass` or `revise`; the model's text is advice (`docs/role-prompts.md`).  The record is five files in the case folder:  `input.json`, `results.json`, `evaluation.json`, `trace.jsonl`, and `case.json`.

The shake-down is a rehearsal.  Its files are kept as a fallback but are not the final recorded pass.  The freeze of the contract and the parameter table comes at its end, so that a flaw the shake-down shows is fixed first.

## Before the shake-down

Every box must be checked by the person named.  A box that cannot be checked means the shake-down waits.

| Needed | Owner | Checked |
|---|---|---|
| The offline harness is on `develop` (#74 merged into `develop`, not `main`) | Anastasiya | [ ] |
| The role runner and the prompts are on `develop` (#60) | Valerie | [ ] |
| The live provider exists:  it calls Claude through LiteLLM, reads the key from `.env`, and never prints it (`docs/runtime-provider.md`) | Anastasiya | [ ] |
| The Developer wiring exists:  the fixed `run_model` tool reached through the role loop | Anastasiya | [ ] |
| `python scripts/check_key.py` prints `OK: HTTP 200 from claude-sonnet-5-5` on the day | whoever holds the key | [ ] |
| The LiteLLM path is tested once (Tue 2026-10-27, 09:30 ET) | Valerie | [ ] |
| The installed packages match `requirements.txt`:  run `pip install -r requirements.txt` again after every pull or merge that changes that file (once #100 merges, tool calls need `litellm[mcp]`, and a plain `litellm` fails before any reply) | whoever runs the pass | [ ] |
| The two research files pass the parameter validator | either | [ ] |
| The working tree is clean and `develop` is at the commit that both owners name | either | [ ] |

## Who runs what

- Whoever holds the key runs every command that uses it.  Claude Code never reads `.env`, never prints a key, and never runs a command that uses one.
- Claude Code may read the saved case folders afterward.
- The held-out history batch is not part of this pass.  It is run once, after the freeze, by Valerie or Anastasiya, never by Claude Code (`docs/history-preregistration.md`, #62).

## Steps of the shake-down

1. Start from the agreed commit.  `git status` shows a clean tree; `git log -1` shows the commit; write both down.
2. `python -m pytest`.  Write down the number of tests that pass.
3. `python scripts/check_key.py`.  Expect `OK: HTTP 200` and exit code 0.  If not, stop and read "If something fails".
4. Run one offline case first, which needs no key:  `python -m harness --preview --seed 7 --months 36 --output runs/shakedown-offline-1`.  Expect status `pass` and exit code 0.  This shows that the harness itself works before a live call is added.
5. Run the live case (whoever holds the key):  `python -m harness.live_case --preview --live --seed 7 --months 12 --output runs/shakedown-live-1` (the settings of the saved 2026-10-27 run, so the two can be compared; `docs/live-workflow.md`).  Expect status `pass`, at most 12 model calls, and the line "Evidence read check (graded by code): pass" in `live-summary.md`.  Use a new folder each time; the harness never overwrites one.
6. Read `trace.jsonl` line by line.  Check that each step is one numbered line; that each model step names the prompt version; that no key-like text appears; and that every cut text is marked as cut.
7. Read `case.json` and `evaluation.json`.  Check that the status follows the code checks, that each issue has a code, a message, and a requested change, and that the model's explanation is at most 150 words per issue.
8. Run one hand-back example:  a case with one required gap, so that the request goes out once, the single round runs, and the case stops on an unresolved gap (`docs/handback-path.md`).  Command (proposed by Anastasiya; scripted, so it needs no key):  `python -m harness.handback_example --output runs/shakedown-handback-1`.  Expect `Case stopped` on the female home range gap and exit code 1; the diet gap is logged as a limitation.  Copy the folder to `hand-back/` in the fallback bundle.
9. Copy the case folders into the fallback folder with a note of the commit, the seed, the date, and the time (`docs/demo-plan.md`, "The fallback").  Before anything is committed:  (a) read each `trace.jsonl` and `roles.jsonl` line by line (step 6), because since #129 a trace holds the full prompts and tool results and the redaction works by pattern only; (b) run `git status` to see which trace files and run folders are present, and add files by name (`git add <file>`), never `git add .` or `git add -A`; (c) once #133 merges, `trace.jsonl`, `roles.jsonl`, and `runs/` are ignored, so a trace that you have read and chosen to commit needs `git add -f <file>`.  Commit them in a small pull request; never add `.env`.
10. Ask one question before the freeze:  did any step show a flaw in the contract (the schemas) or in the parameter table?  If yes, fix it in a commit that says why, run the tests, and repeat steps 4 to 8.  If no, freeze.

## The freeze (Friday 2026-10-30, midday)

Fill the four items in `docs/history-preregistration.md` under "TO FILL at the freeze":  the commit hash of the code that will run; the hashes of the two research files (`python -c "from validators.handoff_hashes import file_sha256; print(file_sha256('data/parameters/iberian_lynx_baseline.csv')); print(file_sha256('data/parameters/sources.csv'))"`); the Python version (`python --version`); and the date and the name of the person who runs the history test.  Commit them in one commit that says why, and merge it before the run.  A change to the contract or the table after this commit means a new run ID and a re-run of every saved result.

## Final recorded runs (after the freeze, by Fri 2026-10-30, 18:00 ET)

| Run | Needs the key | Command (README) |
|---|---|---|
| History test, once, seed 20261101 (it always runs the final evidence gate) | no | `python -m simulation.history --run-seed 20261101 --output history-run-1` |
| Trial batches, 100 pilot and 500 final trials per cell | no | `python -m simulation.experiments --preview --stage pilot --seed <seed> --trials 100 --months 120 --output batch-1` (for the 500-trial final batch, use `--stage final --trials 500`; `--stage` has no default) |
| One live pass through the three roles | yes | **TO FILL** (Anastasiya) |
| One hand-back example | no (scripted; proposed) | `python -m harness.handback_example --output final-handback-1` (copy to `hand-back/` in the fallback bundle) |

Each command writes its output folder inside the repository.  Treat every `trace.jsonl` and `roles.jsonl` in them as in step 9:  read it before it goes to Git, Slack, a slide, or an email.

## If something fails

| What you see | What to do |
|---|---|
| A command prints "refused by the evidence gate" and exits with code 2 | A parameter is `not_checked`, or the evidence file is missing, and the run is final.  Do not edit the file to get past it:  check the contradiction for that parameter, record the result in the evidence file, and run again.  A pilot run only warns. |
| `check_key.py` exit 2 with a 401 or 403 | The key was rejected.  Ask LaNice for a new one-time link.  Do not retry in a loop. |
| `check_key.py` exit 3 | No connection.  Check the network once; if it persists, use the fallback files. |
| `check_key.py` exit 5 | The `.env` file or the key has a bad character.  Fix the file; never paste the key into a chat or a document. |
| A transient provider error (a timeout, a connection reset, HTTP 429, or HTTP 5xx) | The harness may retry at most 1 per tool call, 3 per round, and 10 per case (these limits are a guess; `docs/handoff-decisions.md`).  When a limit is reached, the case stops and reports. |
| Any other provider error, or model output that fails a check | No retry.  The case fails with the reason.  Keep the trace. |
| Case `rejected` (a changed research file, or a hash mismatch) | No retry.  Find what changed.  Start a new run ID. |
| Case `stop` | Read the unresolved issues.  The Developer had up to three revision rounds; both owners are named in `case.json`. |
| Case `failed` | Read the reason in `case.json`.  Never re-run silently:  keep the failed trace and say what happened in the report. |
| The model asks for a tool that is not its own, or source text asks for an action | The code refuses it and never runs it.  Keep the trace line; it is evidence for the report. |
| A live call fails on the day of the demonstration | Switch to the saved outputs and say so (`docs/demo-plan.md`). |

## Not decided yet

- The time limit of the shake-down if it is not clean at 19:30 ET on Thursday:  fix what it found on Friday before the midday freeze, or freeze with the known flaw recorded as a limit.
- Who runs the final live pass if only one of us is free on Friday.
- Whether the demonstration shows a live call at all (`docs/demo-plan.md`, "To agree").
