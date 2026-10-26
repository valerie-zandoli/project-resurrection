# Runtime provider decision (PROPOSED, needs both partners)

Drafted 2026-10-22 by Valerie with Claude Code.  The Agent PRD says the runtime provider and authentication are undecided.  This record proposes an answer so both partners test the same behavior.

## Proposal

- The runtime agents use Claude through LiteLLM. The shared model is `anthropic/claude-sonnet-5-5` (the plain API id is `claude-sonnet-5-5`), chosen by Valerie on 2026-10-26; Anastasiya's agreement is pending.  The plain API id passed `scripts/check_key.py` on Valerie's key on 2026-10-22 and 2026-10-24; through the adapter it has not been checked yet (see Implementation status).
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

## Implementation status

The harness now has a LiteLLM adapter in `harness/litellm_provider.py`. It uses
`ANTHROPIC_API_KEY` from the ignored local `.env` file or the process environment,
limits each request, exposes only the role's allowed tools, and keeps the API key
out of messages and traces. The default model is `anthropic/claude-sonnet-5-5`; set `CLAUDE_MODEL` to override it.  LiteLLM's quickstart shows `anthropic/claude-sonnet-5`, which also worked on Valerie's key, but the pair uses one model for every run.
The provider choice and shared model setting remain pending partner agreement.

Run `python scripts/check_litellm_provider.py` for one short live connection check.
Valerie ran it on 2026-10-26 with litellm 1.106.4 and the model `claude-sonnet-5`, before the shared model was set to `claude-sonnet-5-5` (below); it printed `Claude connection works`.  `litellm` is pinned to that version in `requirements.txt`.  **TO DO (Valerie, before the live pass):**  run `python scripts/check_key.py` and `python scripts/check_litellm_provider.py` again with `claude-sonnet-5-5`, and record the result here.
The regular test suite uses a local stand-in and makes no API calls.

References checked 2026-10-26:

- [LiteLLM Python SDK quickstart](https://docs.litellm.ai/docs/learn/python_sdk_quickstart)
- [Anthropic model deprecations and current model status](https://docs.anthropic.com/en/docs/about-claude/model-deprecations)
