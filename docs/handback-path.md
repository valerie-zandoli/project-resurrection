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
