# Runtime provider decision (PROPOSED, needs both partners)

Drafted 2026-10-22 by Valerie with Claude Code.  The Agent PRD says the runtime provider and authentication are undecided.  This record proposes an answer so both partners test the same behavior.

## Proposal

- The runtime agents use Claude through LiteLLM, with model id `anthropic/claude-sonnet-5-5` (the model id and method LaNice gave on 2026-10-06; older Claude models no longer work).
- Each partner uses a personal key from LaNice's one-time link, stored only in a local `.env` (see `.env.example`).
- Valerie keeps Claude Code and Anastasiya keeps Codex as coding tools.  The runtime agents use one provider so a result does not depend on who ran it.

## Key rules (from LaNice, Day 10)

- The link disappears when opened; have the project open first and paste the key straight into `.env`.
- Never save a key in Slack, Google Docs, notes, screenshots, or GitHub.
- If the link expires before the key is saved, ask LaNice for a new one.  Never ask a teammate to share a key.
- The repository is public:  `.env` is ignored and a test keeps it that way.

## Open actions (people, not code)

- Valerie:  her new-key request to LaNice (sent 2026-10-20) is unanswered.
- Anastasiya:  request her own key.
- Both:  one-call key test (a greeting from Claude) once the provider code exists.

## Decision

Pending.  Reply "yes" or the change you want.
