# Permission boundaries between the roles (DRAFT)

Written 2026-10-29 by Valerie with Claude Code, from LaNice's lesson of 28 October, "Permission Boundaries Between Agents", and its Team Debrief:  audit each agent out loud, as a table, for access it does not need and for any handoff path through which one agent could act through another's broader access.  LaNice's slides are teaching material (`AGENTS.md`); this file audits our own architecture.  Nothing here is agreed until Anastasiya says yes.

## The answer first

No role holds access that its job does not need, and no handoff carries one role's access to another.  Each role holds one tool, and code, not the prompt, refuses everything else.  Two handoffs deserve a watch:  the Researcher's answer and the code-made issues both enter the Developer's task as text.  Neither can change what runs, because the Developer's only tool takes no arguments.  The boundaries are tested with scripted replies, in `tests/test_permission_boundaries.py` and the tests named below.  They have not been tested against a live model that tries to attack; one live pass has run.

## Step 1:  each role as a table

| Role | Its one tool | What the tool can read | What the tool can change | Secrets | Enforced by (CODE or PROMPT) | Pinned by |
|---|---|---|---|---|---|---|
| Researcher | `read_research(key)` | The three snapshot files only (parameters, sources, evidence); an unknown key raises an error | Nothing; the snapshot files are read-only (mode 444) | None | CODE:  `ROLE_TOOLS` in `harness/roles.py`; the fixed keys in `harness/three_role_preview.py` | `test_unknown_research_key_fails_without_reading_arbitrary_files`; `tests/test_permission_boundaries.py` |
| Developer | `run_model()` | The validated input and the snapshot, checked as unchanged before the run | The case's results, through the fixed simulator, once per round, with no arguments | None | CODE | `test_duplicate_execution_is_not_silently_run_again`; `test_the_developer_cannot_pass_arguments_to_run_model` |
| Evaluator | `check_artifacts()` | The input, the results, and the snapshot, through the code check | Nothing it can save; the verdict is built by code (`build_evaluation`), and the model only explains it | None | CODE:  once per round; the verdict is schema-checked and must carry the run's identity and every required check (#127) | `test_a_second_check_artifacts_call_fails_and_is_not_run_again`; `tests/test_harness_contracts.py` |
| Harness (ordinary code, not a model) | Everything: snapshot, hashes, the revision limit of 3, the provider | `.env`, which holds the API key | All case files | The API key | CODE:  the key goes only into the request to the provider (`harness/litellm_provider.py`), never into a message; a printed provider shows `api_key=[redacted]`; traces redact key-like text | `tests/test_litellm_provider.py`; `tests/test_trace_context.py` |

A role needs a new tool only through a code change:  `ROLE_TOOLS`, plus the `tools:` line of its prompt, which `load_prompt` checks against the harness (`test_a_prompt_whose_tools_differ_from_the_harness_is_refused`).  That change is a pull request with one approval, which is LaNice's "ask explicitly, with a reason, and have it approved".

## Step 2:  access a role holds but does not need

None found.  For each permission I asked what breaks if it is taken away:  without `read_research` the Researcher reads nothing, without `run_model` the Developer runs nothing, and without `check_artifacts` the Evaluator checks nothing.  Two facts to know, neither a defect:

- One API key and one model setting serve all three roles.  Each role has its own provider object, but no role can read the key; only the harness holds it.
- The harness holds everything.  It is code that is reviewed by pull request, not an agent.

## Step 3:  handoff paths, and acting through another agent

| Path | What crosses | Could the receiver act with the sender's access? | Enforced by |
|---|---|---|---|
| Researcher to Developer | The Researcher's answer, cut to 2,000 characters and wrapped as untrusted data | No.  The Developer's tool takes no arguments, so no text can steer it.  A planted instruction in a source can reach only the words of a prompt. | CODE (no-argument tool); the wrapper is a request to the model, not a guarantee |
| Evaluator to Developer | The code-made issues (code, message, requested change), wrapped as data | No, for the same reason | CODE |
| Developer to Evaluator | `results.json` | The code check recomputes from the files; the Developer's words do not set the verdict | CODE |
| Evaluator to harness to person | `evaluation.json`, whose status comes from code | The harness routes by that status; the model's explanation never changes it | CODE |
| One role to another role directly | Nothing:  no such path exists | A role that asks for another role's tool is refused ("may not call"), and the case fails | CODE:  `test_a_role_that_asks_for_another_roles_tool_is_refused_and_the_case_fails` |

## What would change this audit

- If the Developer ever writes or runs generated code, its access grows (files and execution).  Re-run this audit, and read `docs/execution-sandbox.md`, first.  Today it runs one fixed simulator.
- Any new tool, or any tool that takes arguments, needs a new row and a new test.
- Inside a batch run there is no human approval step; a person reads the results afterward.  LaNice's "approved" step is pull-request review today.

## What this does not show

The tests use scripted replies, not a model that tries to attack.  One live Claude pass has run, and it is an integration run.  The wrapper around source text asks the model to treat it as data; the guarantee is that no text can change what the fixed tools do.  A source that is false is a different failure (`docs/failure-taxonomy.md`).
