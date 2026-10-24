# Handoff decisions (PROPOSED)

Drafted 2026-10-22 by Valerie with Claude Code; clarification and failure wording revised with Anastasiya. This document proposes the research contract and harness behavior for partner review. User-approved simulator assumptions remain valid unless explicitly superseded. The checks and policies described here must not be claimed as implemented until verified in code. Numbers marked (guess) are provisional; measured outcomes are recorded separately.

## Research contract

1. **Confidence.**  The allowed labels are `low`, `medium`, and `high`, and `confidence_reason` is required (one sentence that names the evidence).  `high` means two or more distinct origins, each read in full, and no open conflict.  `medium` means one origin read in full, or two or more distinct origins with a recorded conflict.  `low` means abstract only, second-hand, provisional, or an assumption.  Valerie assigns the label, because it is an evidence judgment.  Code checks that the label is in the set and the reason is not empty.
2. **Origin.**  Origin IDs are defined in `docs/research-notes.md`.  The registry `origin` lists every upstream that a source reports; it is a menu, not a count.  The parameter table gets an `origin` column that lists only the origin IDs that support that row's value, and the validator checks that they are a subset of the origins of the sources cited in the row.  For example, `eu_spain_report2018` reports both Palomares 2001 and the 2017 census, but only `palomares2001` supports a rabbit threshold.  Code counts distinct row-level origins per parameter, not source keys.  `unknown` never counts as an independent origin.  Provisional and final figures of one census share an origin; different census years are different origins.  Code sets no minimum number of origins; a single-origin parameter can still be used, and its confidence label says how far to trust it.
3. **Contradictions.**  The parameter table gets a `contradicts` column, and every row has a value.  Entries are separated by semicolons:  `none_identified`; `not_checked`; `source:<key>~source:<key>` (two sources of this row disagree about this parameter); and `parameter:<name>` (this parameter conflicts with the evidence for another parameter, such as range size and food level).  `none_identified` and `not_checked` stand alone.  The validator checks that every named key and parameter exists.  A `not_checked` row warns in pilot runs and blocks final runs.  A recorded conflict does not block a run (both versions run, as agreed for range size), but the Evaluator report lists every open conflict.  A test holds the known conflicts from `docs/research-notes.md` (breeding age, `palomares2005` against `catsg`; range size and food) and fails if they are missing from the column.

## Clarification round

- A case is one run chain, from the first `input.json` until pass or stop.  A deliberate change to the research files starts a new run (round 0) inside the same case; the clarification budget carries over.
- Each case gets one Researcher round, shared by the Developer and the Evaluator, and it batches every open parameter.  The budget is separate from developer revisions 1 to 3.
- A request names the case and run IDs, parameter, missing information, required or optional classification, reason for that classification, who filed it, and the evidence or correction needed for resolution.
- A required gap prevents a defined experiment from running or being interpreted under its agreed assumptions: for example, a missing value or unit, an invalid range, an unresolved contradiction with no agreed scenario treatment, or a specific scientific defect documented by the Evaluator. An optional gap does not prevent the agreed experiment; log its effect and limitations.
- Low confidence alone does not make a gap blocking. An explicitly approved provisional value may be used with its source-access caveats, rationale, and agreed sensitivity range. In particular, the agreed post-dispersal annual mortality of 0.37 with sensitivity 0.10–0.50 is not rejected solely because its evidence is an older abstract. The Evaluator may identify a specific additional defect, but must explain it rather than treating the label itself as failure. This does not waive schema validation or the separately agreed audit policy.
- Resolution requires a documented answer that addresses the request, complete handoff fields, and passing structural/reference checks. Appropriate answers include correcting units, locating a passage in an existing source, recording a contradiction with an agreed scenario treatment, supplying new evidence, or documenting an explicitly approved assumption. Preserve unknown provenance as unknown; do not invent a source or independent origin for an assumption.
- A new independent origin is required only when the request specifically concerns missing independent support. The validator checks fields and references; the Evaluator reviews whether the answer addresses the scientific gap. Human approval is needed for a new assumption or change in scope. Neither a validator pass nor a confidence label alone establishes scientific resolution.
- A required gap that remains after the round, or a new required gap after the round, stops the case and reports to both owners.  An optional gap never stops a case.

## Failure behavior (for the PRD)

- **Hand back, once.** Use the single batched Researcher round for gaps that evidence or clarification can address. The request specifies what would resolve the gap; it does not require a new study by default.
- **Escalate** to Valerie and Anastasiya if a required gap remains or a new required gap appears after the clarification round. Stop the case with its table, request, response, and unresolved reason preserved. Human review may authorize a revised experiment, but never silently resets the exhausted case budget. Optional gaps remain disclosed limitations.
- **Reject the affected artifact or attempt without transient retry** for a schema mismatch, stale input file, killed run, or unresolved developer issue at revision round 3. Report the specific reason. Existing schema/hash helpers support some checks; end-to-end harness enforcement remains to be built. A deliberate research correction uses a fresh validated input and run ID while retaining the same case-level clarification budget.
- Record clarification outcome as `resolved_with_evidence`, `resolved_with_approved_assumption`, or `unresolved`, with the evidence/correction, reviewer, and reason. An approved assumption remains labeled as an assumption; it is not a verified scientific fact. Code may check source references and recorded provenance but cannot establish scientific independence merely by extracting a page identifier.
- Keep the primary-source audit below separate from clarification success. As a provisional operational check, if fewer than 6 of the first 20 clarification cases resolve their required gaps (guess), review the hand-back policy with both owners before later cases. Report evidence-based and assumption-based resolutions separately. Do not penalize successful clarification solely because it reused an existing source, and do not change the held-out historical tolerance in response to these outcomes.

## Hashes

The harness computes the content hashes from the actual input files, and the agents carry them unchanged.  A deliberate research edit starts a fresh run.  No live harness enforcement exists yet.

## Transient retries

- Allow at most 1 retry per tool call, 3 per round, and 10 per case (guess).
- These errors qualify:  a network timeout, a connection reset, HTTP 429, and HTTP 5xx from the provider.  These do not:  a schema or validation failure, model output that fails a check, a killed run, and any other 4xx.
- The trace logs each retry with its error, apart from revisions.  When a bound is reached, the case stops and reports.

## Primary-source audit

- Before each experiment batch, a person checks 10 parameter rows against the primary source.
- A script chooses the rows with a recorded seed (the batch run ID), so another person can reproduce the sample.
- A failure means the value or range does not match the primary source, or the source does not support the claim.  A primary source that cannot be reached counts as a failure, reported separately as "unavailable".
- Below 9 of 10, the batch stops; fix the rows, look for the same fault in the unsampled rows, and draw 10 fresh rows.
- One running table records batch, rows checked, correct, unavailable, and the running total.  Review the audit design if the running total falls below 90% after 30 rows (guess).
- A trace that reports zero missed contradictions proves nothing.  The planted flaws 7 and 8 in `docs/baseline-test.md` test for them.

## Labels and the held-out tolerance

Label every threshold "guess" or "measured".  Change a future threshold only in a commit that says why.  The historical tolerances (growth within 0.05 of 1.17; the 2011 count within 10%) never change after the held-out result is seen.

## Still open

Sandbox limits and the isolation mechanism, the trace location and retention, and the writer of the shared state need Anastasiya's answers (`docs/execution-sandbox.md`, `docs/trace-plan.md`, `docs/architecture.md`).
