# Trace plan: find the first wrong turn (DRAFT, needs the harness pair)

Drafted 2026-10-22 by Valerie with Claude Code, from LaNice's Agent Traces lesson:  a trace is the receipt of one run, and the fix depends on whether the wrong turn was a prompt gap, a harness issue, or a tool problem.  Extended 2026-10-27 from her "Tracing a Multi-Agent System" slides (follow a task across an agent boundary); the slides are teaching material, and our architecture stands.

## What the harness writes

One file per run, `runs/<run_id>/trace.jsonl`, with one line per step:

- step number and role;
- prompt version;
- content hashes of the input files (pull request 9);
- the model message;
- the tool requested, with its arguments;
- a summary of the tool result, with the characters the tool returned (`sent_chars`) and the characters the model received (`received_chars`);  a difference means the harness cut or redacted text before the model saw it;
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

## Following a task across a handoff

A trace can hold a handoff failure that no single step shows.  Three rules from LaNice's slides:

1. **A handoff begins when one role sends and ends when the next role has it in its context.**  Sent is not the same as received; failures hide between the two.
2. **Compare what was sent with what was received.**  For files, the content hashes do this (`check_handoff_hashes`), but a hash only shows that the same bytes were stored, not that the model read them all.  For text a model reads, compare `sent_chars` with `received_chars` on the tool-result line.
3. **Work backward from the first wrong step and check its input.**  Wrong input means the problem is in the handoff (the harness trimmed or dropped it, the tool returned it wrong, or the role before sent it wrong).  Right input means the problem is in the reasoning (a prompt gap or a model error).

For a table of any trace, add two columns to the six steps above:  *reasoning or harness* (who made the wrong turn) and *sent versus received* (the two numbers).

### Worked example:  the 2,000-character cut (found 2026-10-26)

From the first live pass (2026-10-26, pull request 100) and `harness/roles.py` before pull request 107.  The harness cut every tool result to 2,000 characters before the model saw it, and the cut left no record.

| Step | What the trace line shows | Reasoning or harness | Sent versus received |
|---|---|---|---|
| 1 | Researcher asks for `parameters`; `cut 1683 characters` | Harness:  the model got the first 2,000 characters | The file has 13,915 characters; the line shows only a cut counted from 2,083 |
| 2 | Researcher asks for `sources`; `cut 1683 characters` | Harness:  the same limit | The file has 17,973 characters; the note is identical to step 1 |
| 3 | Researcher says "Both reads came back cut off" | Reasoning was right; its input was wrong | The Researcher itself reported the gap |
| 4 | Developer's `run_model`; `cut 1600 characters` | Harness:  the same limit again | A result of any size shows a note counted from 2,000 |

The first wrong step is step 1, not step 3.  Two clues put the problem in the handoff and not in the model:  two files of very different sizes show the same cut note, and the receiving role says it was handed a partial text.  Pull request 107 raised the limit to 40,000 characters.  With `sent_chars` and `received_chars`, a future cut shows as two different numbers on the line itself.

## Open decisions for the harness pairing session

- Whether the trace lives in the run directory or in a separate log folder.
- How long to keep traces (the repository is public, so traces must hold no keys or private data).
