# Hand-back path code (PROPOSED)

Written 2026-10-24 by Valerie with Claude Code.  The code is `harness/handback.py`; its tests are `tests/test_handback.py`.  Status:  **TESTED ONLY**.  The rules exist as code and a named test runs each one, but no harness calls them yet.  The harness is the pair's job, so this is a starting point for the pairing session, not a finished harness.  Nothing here is agreed until Anastasiya says yes.

## What it guarantees (from `docs/handoff-decisions.md`)

| Rule | Where it lives in the code |
|---|---|
| A request names the case, the run, the parameter, what is missing, required or optional, the reason for that class, who filed it, and what would resolve it | `Request` (every field is required) |
| One Researcher round per case, shared by the Developer and the Evaluator, batching every open parameter once | `Case.open_round` (a second call raises `BudgetExhausted`) |
| A deliberate research change starts a new run inside the same case; the spent budget carries over | `Case.start_run` |
| A resolved answer needs an answer text and a named reviewer; an assumption stays labeled as one | `Response` |
| A required gap left unresolved, or missing a response, stops the case and reports to Valerie and Anastasiya | `Case.close_round` |
| An optional gap never stops a case; it is a logged limitation | `Case.close_round`, `Case.new_gap` |
| A new required gap after the round stops the case and never opens a second round | `Case.new_gap` |
| Transient errors only (timeout, connection reset, HTTP 429, HTTP 5xx) are retried; a schema failure, stale input, killed run, failed model-output check, or other 4xx is recorded and never retried | `classify_fault`, `Case.retry` |
| At most 1 retry per call, 3 per round, 10 per case; at a bound the case stops and reports | `Case.retry` |
| The report keeps the table-side facts a person needs and resets nothing | `Case.report` |

The three retry bounds and the 6-of-20 review bar are guesses, as in the decisions document.

## What it does not do

- It sends no message.  `report()` names both owners in `notify`; the harness must deliver it.
- It calls no model and judges no science.  Whether an answer addresses the gap is for the Evaluator and a person.
- It does not check the parameter table; the validator does.
- It does not count developer revisions (rounds 0 to 3); `docs/evaluator-checks.md` covers that stop.
- It does not yet have a schema file for requests and responses; add one when the pair agrees on the shape.

## The hand-back example (proposed by Anastasiya, 2026-10-27)

`python -m harness.handback_example --output hand-back` runs these rules once on two real gaps in the research files, with scripted answers in place of a model, so it needs no key.  The Evaluator files one batched request:  a **required** gap, a measured female home range for Andujar-Cardena (the 10 km2 average comes from a web summary that names no study, and the model uses the home range to count territories), and an **optional** gap, a primary study for the rabbit share of the diet (the model does not use it).  The scripted Researcher answers both as unresolved.  The case stops on the required gap and names both owners, the optional gap becomes a logged limitation, and a second round is refused.  It writes `case.json` and `trace.jsonl` in the shape that `scripts/check_fallback.py` expects for `hand-back/`, and every screen it prints starts and ends with the caption "scripted hand-back example; no model is called".  Tests:  `tests/test_handback_example.py`.  It shows the code path, not a Researcher's judgment; a live hand-back needs the roles to file requests, which is not built.
