# First three-role preview

This adds one thin integration path on top of `run_case`, using the existing
research snapshot and numerical simulator. Run from the repository root in the
Python 3.12 environment:

```sh
python -m harness.three_role_preview --preview --seed 7 --months 12 --output /tmp/lynx-three-role-1
```

Use a new output folder each time. The command needs no key and calls no network.
Its role replies are explicitly scripted fixtures. The numerical simulation and
artifact checks really run; this is not a live Claude evaluation or a historical
test. It does not use the held-out history count.

## Jobs and handoffs

1. The existing harness validates both research tables, snapshots them, and
   computes their content hashes. Invalid tables stop before any role runs.
2. Researcher reads the two snapshot tables through `read_research` using only
   the keys `parameters` and `sources`. Reading both is required before execution.
   This role inspects existing work; it does not establish source accuracy or
   generate a new parameter table. Existing role-runner text truncation applies,
   so this is not proof the complete evidence was reviewed.
3. Developer receives the Researcher explanation as marked untrusted advice.
   Its only tool is the fixed `run_model`, with no model-controlled arguments.
   It runs once per round against the recorded configuration and unchanged snapshot.
4. Evaluator starts a separate conversation. Its `check_artifacts` tool inspects
   the actual configuration, numerical output, and research snapshot. The code
   verdict controls the result; an explanation saying “pass” cannot override it.
5. Issues return to the Developer for revisions 1–3 after initial round 0.
   Research inspection runs once. The fixed simulator cannot repair code, so an
   unresolved implementation problem requires human work and eventually stops.

All roles retain the existing four-step cap and per-role tool allowlist. Missing
required tool use, unknown research keys, duplicate numerical/check execution,
and provider failures stop the case without automatic retries. No generated code
is executed. The preview does not implement researcher clarification or expand
the draft execution sandbox policy.

## Inspectable records

Existing `case.json`, `trace.jsonl`, snapshot, and per-round `input.json`,
`results.json`, and `evaluation.json` remain the authoritative records.
`roles.jsonl` records role/tool steps with prompt versions and input hashes.
Per-round `researcher.json` (round 0 only), `developer.json`, and `evaluator.json`
hold scrubbed explanations, tool names, and step counts. These explanations are
advice. `pipeline.json` labels the mode and limitations. Historical validation
remains `not_assessed`.

The function `run_three_role_case` accepts one provider per role for later
integration. Non-fixture providers are labeled `provider_supplied_unverified`;
their presence is not proof of a successful live call. The default command stays
scripted until the Claude adapter and its connection have been reviewed and tested.
The Developer prompt is a new preview prompt; existing Researcher/Evaluator
prompts and shared contracts are reused without changes.
