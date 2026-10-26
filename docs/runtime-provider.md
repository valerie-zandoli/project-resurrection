# Runtime provider decision (PROPOSED, needs both partners)

Drafted 2026-10-22 by Valerie with Claude Code.  The Agent PRD says the runtime provider and authentication are undecided.  This record proposes an answer so both partners test the same behavior.

## Proposal

- The runtime agents use Claude through LiteLLM. The model id in the original proposal, `anthropic/claude-sonnet-5-5`, has not been verified against the current provider documentation.
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
out of messages and traces. The default model is `anthropic/claude-sonnet-5`,
which the current LiteLLM quickstart documents; set `CLAUDE_MODEL` to override it.
The provider choice and shared model setting remain pending partner agreement.

Run `python scripts/check_litellm_provider.py` for one short live connection check.
That check has not been run from this checkout because it has no local `.env` key.
The regular test suite uses a local stand-in and makes no API calls.

References checked 2026-10-26:

- [LiteLLM Python SDK quickstart](https://docs.litellm.ai/docs/learn/python_sdk_quickstart)
- [Anthropic model deprecations and current model status](https://docs.anthropic.com/en/docs/about-claude/model-deprecations)
