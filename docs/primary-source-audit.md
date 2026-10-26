# Primary-source audit (PROPOSED)

Written 2026-10-25 by Valerie with Claude Code.  It carries out the audit in `docs/handoff-decisions.md` (item 7 of `docs/handoff-build-checklist.md`).  Nothing here is agreed until Anastasiya says yes.

## What it is for

The parameter validator checks structure only.  A person must also check that a value matches its primary source.  Before each experiment batch, a person checks 10 parameter rows; the bar is 9 of 10 correct.

## Draw the rows

```bash
python scripts/audit_sample.py --run-id <batch run ID> --output audits/<batch run ID>.md
```

The seed is the first 8 bytes of the SHA-256 of the run ID, so another person gets the same 10 rows.  The sheet lists, for each row, the value, the range, the sources, and how each source was read.  Use a new file name each time.

## Record the result

For each row, write `correct`, `incorrect`, or `unavailable` (a source that cannot be reached is reported apart) and one line of note.  Then fill the running table at the bottom of the sheet.  Below 9 of 10 the batch stops:  fix the rows, look for the same fault in the rows that were not drawn, and draw 10 fresh rows with a new run ID.  Review the audit design if the running total falls below 90% after 30 rows (a guess).

## Limits

- Ten rows from 23 is a small sample; the running total across batches is the better signal.
- A row whose only source was read as an abstract can be checked only against the abstract.  Read that source in full first if the row is drawn (`docs/unread-sources.md`).
- The script chooses rows; it does not judge them.
