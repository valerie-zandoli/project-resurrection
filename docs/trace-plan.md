# Trace plan: find the first wrong turn (DRAFT, needs the harness pair)

Drafted 2026-10-22 by Valerie with Claude Code, from LaNice's Agent Traces lesson:  a trace is the receipt of one run, and the fix depends on whether the wrong turn was a prompt gap, a harness issue, or a tool problem.

## What the harness writes

One file per run, `runs/<run_id>/trace.jsonl`, with one line per step:

- step number and role;
- prompt version;
- content hashes of the input files (pull request 9);
- the model message;
- the tool requested, with its arguments;
- a summary of the tool result;
- the validator verdict;
- the evaluator status and the revision round;
- any text the harness removed or cut, so truncation is visible.

Hand-authored fixtures stay labeled `sample`.  Never present them as traces.

## How to read a trace

1. Start at step 1, not at the bad answer.
2. Mark the first wrong step, not the last one that looks bad.
3. Check the step before it:  did it give the agent what it needed?
4. Name the decision in one plain sentence.
5. Sort the cause:  a prompt gap (the model never got a rule), a harness issue (the code skipped a check, a limit, or an error path), or a tool problem (bad, empty, or confusing data).
6. Fix that one cause, add a row to `docs/regressions.md`, and add the test or eval case in the same commit.

## Open decisions for the harness pairing session

- Whether the trace lives in the run directory or in a separate log folder.
- How long to keep traces (the repository is public, so traces must hold no keys or private data).
