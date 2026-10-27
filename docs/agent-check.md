# Is each role an agent? The five-part check (DRAFT)

Drafted 2026-10-27 by Valerie with Claude Code, from LaNice's Learn slides "Is Your Agent Really an Agent?" (posted in the class channel on 2026-10-27).  The slides ask for two things:  check each agent against the five parts (the language model, context, tools, chosen success criteria, and a loop), and structure its loop as observe, think, act, check, with a clear way to stop.  The slides are teaching material; our architecture stands (`AGENTS.md`).  This file does both checks and says what is missing.

Status tags:  **CODE** (merged and tested), **IN REVIEW** (an open pull request), **PLANNED** (not built), **PROMPT ONLY** (the model is asked; nothing checks).  The tags are true on the day of this pull request.  Update them in the same pull request as the code that changes them.

## The answer first

On `develop`, all three roles have the five parts, but only the Researcher's loop leaves the model a choice (which file to read next); the Developer and the Evaluator may make one tool call each.  The slides' test is "if you can draw every path in advance, it is a workflow, not an agent", and we can still draw every path:  the Researcher reads three files and answers; the Developer calls one tool once, with no arguments; the Evaluator calls one tool once.  The code decides the verdict, and the model writes the explanation.  That follows our rule "a prompt asks; code guarantees", but it limits what we can say.  Today the system is best described as **three roles run by a harness**, with the closest fake being a **fixed chain** (table below).

Two choices for the owners, not decided here:

1. **Name what runs.**  Call the Developer a tool and the other two roles agents ("two agents and one tool"), or call all three "roles" and keep the word "agent" for a role whose next action the model picks.  The demonstration should claim no more than the table shows.
2. **Give a role a choice, or do not.**  A Researcher that picks which source to read next within a budget, or that decides to ask for the one clarification round, would use the loop.  A Developer that writes and runs code would too, but that needs the sandbox (`docs/execution-sandbox.md`, still a draft) and is not a task for before the 2026-11-02 demonstration.  The Evaluator's verdict must stay in code.

## The five parts, role by role

| Part | Researcher | Developer | Evaluator |
|---|---|---|---|
| 1. Language model (LLM) | Claude through LiteLLM (`harness/litellm_provider.py`):  **CODE**; the first live pass is **IN REVIEW** (#100, which holds #109); tests use a scripted fake | Same adapter; the prompt says to call `run_model` exactly once and explain, so the model adds words, not a decision (`prompts/developer.md`) | Same adapter |
| 2. Context | A new conversation for each role; the system prompt, the task, and each tool result, scrubbed and marked as untrusted data:  **CODE** (`harness/roles.py`, `harness/three_role_preview.py`) | Same, plus the Researcher's text as advice and earlier issues as data | Same; it never sees another role's conversation |
| 3. Tools | `read_research`, read-only, and no other tool can run:  **CODE** (`ROLE_TOOLS`) | `run_model` only | `check_artifacts` only |
| 4. Chosen success criteria | Set in code before the loop:  all three of `parameters`, `sources`, and `evidence` read, or the case fails:  **CODE**.  Whether the answer is right is not graded on `develop`; a code grade of the low-confidence and conflict rows it names is **IN REVIEW** (#100, which holds #109) | Set in code:  `run_model` was called and the results pass the schema and hash checks in `run_case`:  **CODE** | Set in code:  `check_artifacts` was called, and the tool's evaluation is the record, never the model's text:  **CODE** |
| 5. Loop | `run_role`, at most 4 steps:  **CODE**.  The model picks which file to read next and when to stop | The same loop, but one allowed call, so one pass | The same loop, one allowed call |

## The loop:  observe, think, act, check

| Step | Where it happens | Tag |
|---|---|---|
| Observe:  the goal, the context so far, the last tool result | `messages` in `run_role`:  the task, then each tool result, scrubbed and wrapped | **CODE** |
| Think and act:  the model picks one next action and calls a tool | `provider.complete` returns the calls; the harness refuses a tool outside the role's list and arguments that do not fit | **CODE** |
| Check:  compare the result with the success criteria, then add it to the context | Not on each pass.  The harness checks after the role returns:  the required calls, the schema and hash checks, and the Evaluator's code checks (`run_case`, `validators/results_checks.py`) | **CODE**, once per round |

Our check runs once per round, after the role finishes, not on every pass.  With roles that take one to three passes, that is intended:  the criteria live in code, outside the model.  The slides' loop checks each pass, so a role with a longer loop would need a check inside the loop.

## Ways to stop

| Exit | The rule | Tag |
|---|---|---|
| Success | A test the harness can check, chosen before the loop (part 4 above).  The model ending with a text reply stops the loop, but a case passes only when the code checks pass | **CODE** |
| Limits | At most 4 steps for a role; at most 3 revision rounds; a 1,200-token reply limit and a 30-second timeout with no retries; a reply cut off at the limit fails loudly (#108).  A shared cap of 12 Claude calls per run is part of the live command (`MAX_CALLS`) | **CODE**; the call cap is **IN REVIEW** (#100) |
| Stuck | If the last two passes repeat the same action, stop and report.  Before this rule a repeated call ran to the 4-step cap and ended as "no final answer", which reads as a limit.  An identical result repeated across revision rounds is not detected early; the 3-round cap ends it | **CODE** (#112) |

## Spot a fake agent

| Fake | What it looks like | Do we have it? |
|---|---|---|
| One-shot | One prompt, one answer, so nothing can be corrected | No.  Tool results go back to the model.  A Developer or an Evaluator that answers without its tool fails the case |
| Fixed chain | The steps are hard-coded, so the model never chooses an action | **Closest for the Developer and the Evaluator.**  Each may make exactly one tool call, and the harness fails the case otherwise.  The scripted preview (#94) is a fixed chain by design, and its caption labels it a scripted preview |
| Blind loop | It repeats, but never checks a result and has no way to stop | No.  The step cap, the required calls, the code checks, and the stuck rule (**CODE**, #112) each end it |

Fix first the part that makes the closest fake:  a fixed chain needs a real choice.  The choices in "The answer first" are the options.

## What this file does not show

No live pass is on `develop` yet, so every **CODE** row is tested offline with a scripted model.  The check is a lens on the design, not a measurement; a live model could still act like a fixed chain, or repeat itself in ways the caps do not show.  The five parts are one definition of "agent", taken from teaching material.  Nothing here shows that three roles beat one agent; that comparison is `docs/baseline-test.md`.
