# Regressions: failures found, and what now catches each (DRAFT)

Started 2026-10-25 by Valerie with Claude Code, as `docs/eval-plan.md` asks:  one row for every failure found, with the test or case that now catches it, in the same commit as the fix.  A row that says "no test yet" is a gap to close, not a finished fix.  The cause classes come from `docs/trace-plan.md`:  prompt gap, harness issue, or tool problem (bad, empty, or confusing data).

| Date | What failed | Cause class | What catches it now | Fixed in |
|---|---|---|---|---|
| 2026-10-24 | The PRD, the deck, and the repository PRD said the simulator preview was "in review" after it merged, and said PR #39 was "not yet merged" | harness issue (a status written by hand goes stale) | no test yet; rule:  re-check every status sentence when a pull request merges | #55, the deck update |
| 2026-10-24 | `main` received the simulator after Valerie approved #19 at an older commit, because "dismiss stale approvals" is off | harness issue (a process gap) | no test yet; rule:  name the approved commit in each approval; the setting is an open decision | open |
| 2026-10-24 | The EU report's reading of 1.0 and 4.6 rabbits per hectare as needed densities was copied into our table as thresholds; the primary source says they were enough, not needed | tool problem (a secondary source misread a primary one) | the `contradicts` entry `source:eu_spain_report2018~source:palomares2001` in the draft evidence file (#35); a test that the known conflicts are present is planned in `docs/handoff-decisions.md` and not built | #57, #35 |
| 2026-10-24 | The 2011 Andujar-Cardena total has two values (214 and 202) in our sources | tool problem (conflicting data) | no test yet; both values are in `data/history/counts.csv` and the notes point to the conflict | #57; the choice stays open |
| 2026-10-24 | Food level 1 per hectare, an autumn minimum, is applied as a spring density, so the model gives "extinction at food 1" by construction | prompt gap in the design (an assumption with no label) | the evidence text now says so in the baseline table and the draft evidence file; no test | #57, #35 |
