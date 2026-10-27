# First live Claude workflow

This combines the existing adapter (#91/#98) and three-role preview (#94) on
`resurrection-anastasiya`. Their individual reviews still apply; integration here
does not merge their pull requests into `develop`.

From the repository root with the Python environment active and your personal
key in the ignored local `.env` file:

```sh
python -m harness.live_case --preview --live --seed 7 --months 12 --output /tmp/lynx-live-1
```

`--live` explicitly selects real Claude calls. The default remains the separately
available scripted rehearsal. `--env` can point to another private local key file;
`--model` sets a model override recorded with the run. No key is written to the
output. `live.json` records the actual model names, installed adapter version,
code fingerprints, call counts, status, and seed. Partner agreement on the shared
model remains a separate decision; a successful request proves connectivity only.

The same snapshot, tool restrictions, schemas, and code checks as the scripted
preview apply. Each role starts a separate conversation. Researcher must inspect
both existing tables and the evidence file (#104), Developer calls the fixed
simulator once per round, and Evaluator must call the code checks. Their
explanations cannot replace tool records or a code verdict. The role runner now
passes each research file whole, up to 40,000 characters (#107); this still does
not demonstrate complete source review or autonomous research.

**The saved run in `examples/live_claude_20261026/` predates #104 and #107.**  Its
Researcher saw only the first 2,000 characters of each table (11 to 25 percent of
each file; its own summary says the reads came back cut off) and did not read the
evidence file.  Treat it as an integration check of the live path, not as evidence
that the model read the research.  Replace it with a new live run after this merges.

**After this merges, run `pip install -r requirements.txt` again.**  Tool calls need
`litellm[mcp]`; with a plain `litellm` install the live case fails before any reply.

## The evidence read check

The Researcher's task asks for an answer of at most 150 words that ends with two lines, `LOW:` and
`CONFLICTS:`, naming every parameter whose confidence is low and every parameter with a recorded
conflict.  After the Researcher answers, code compares those names with the evidence file (the same rows
that the evidence gate lists) and records the result in `round_0/researcher.json` (`evidence_check`), in
`pipeline.json`, in `live.json`, and in `live-summary.md`.  A wrong or missing answer does not change the
code verdict, because the Researcher's text is advice; the check shows whether the model read the file
correctly.  The scripted stand-in answers from the file in code, so a scripted pass shows only that the
grader works.

The short answer also keeps the reply inside the adapter's 1,200-token limit.  When the task asked the
Researcher to report every label, a Researcher that saw the whole files wrote a reply that was cut off
even at 4,000 tokens, and the live case of 2026-10-27 failed that way.

There are at most four model steps per role and 12 attempted model calls across
the whole live case. Requests have the adapter's 30-second timeout and no automatic
retries. The existing harness still limits Developer revisions to rounds 1–3
after round 0; the total call limit can stop a live case sooner. The fixed tool
cannot repair generated code, and no generated code executes.

`case.json` and per-round input/results/evaluation files hold the verdict.
`roles.jsonl` holds tool steps; `model-calls.jsonl` holds scrubbed request/reply
summaries, with truncation noted. `live-summary.md` is the readable run record.
The generic `pipeline.json` retains its conservative provider-supplied label;
`live.json` distinguishes a real Claude attempt from an injected-provider test.
Keep failed output folders and use a new output folder for a deliberate new run.

Tests inject stand-in providers and make no API calls. A live run is reported only
after inspecting its saved records. A successful small run is integration evidence,
not historical validation, final scientific experiments, proof of source accuracy,
or evidence that these roles outperform a single agent.

## Observed run, 2026-10-26

The saved example in `examples/live_claude_20261026/` passed on the first
simulation round: 12 synthetic months, seed 7, six completed Claude requests
(two per role), using `anthropic/claude-sonnet-5-5` and LiteLLM 1.106.4.
All recorded code checks passed. The artifacts include the validated input
snapshot, numerical results, role tool records, scrubbed model-call summaries,
and code fingerprints. This is integration evidence only.

An earlier attempt stopped before a model reply because LiteLLM's tool path
needed its `mcp` extra. `requirements.txt` now includes that extra. The failed
attempt was retained locally; the example above is the subsequent deliberate run.
