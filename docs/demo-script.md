# Four-minute demonstration script (DRAFT)

Drafted 2026-10-24 by Valerie with Claude Code.  This is a first draft for Valerie and Anastasiya to rewrite in their own voices.  The presenter split and the times are proposals; nothing is agreed.  `docs/demo-plan.md` (in review, #54) holds the dates and the fallback files; this file holds the words.

Text in [FILL: ...] brackets depends on a run that has not happened yet.  Do not present a bracket as a result.

## Time budget (4:00, with about 20 seconds of slack)

| Clock | Beat | On screen | Proposed speaker |
|---|---|---|---|
| 0:00 to 0:25 | 1. The question | slide 1 | Anastasiya |
| 0:25 to 1:00 | 2. Three roles and the harness | architecture diagram | Anastasiya |
| 1:00 to 1:30 | 3. What runs today | status slide | Valerie |
| 1:30 to 2:15 | 4. One saved run and one hand-back | `input.json`, `results.json`, `evaluation.json` | Valerie |
| 2:15 to 2:55 | 5. The history test | history report | Valerie |
| 2:55 to 3:30 | 6. The grid and its limits | Table 1 and Figure 1 | Anastasiya |
| 3:30 to 4:00 | 7. What stays open | open-decisions list | both |

## Script

**1. The question (slide 1)**

Can a small Iberian lynx population survive for 120 months?  We built a simulation to ask that question, and a team of three agents and one piece of ordinary code to run it with care.  In four minutes we will show how the pieces fit, what has been tested, and what the model cannot tell us.

**2. Three roles and the harness (diagram)**

The Researcher reads the sources and writes the parameters.  The Simulation Developer runs the model.  The Evaluator checks the results.  Between them sits the harness, which is ordinary code:  it passes the files, checks their hashes, takes a read-only snapshot, limits revisions to three rounds, and writes a trace.  The prompts ask; the code guarantees.

**3. What runs today (status slide)**

Every claim carries a tag.  "Tested only" means merged code with a named test that the running system does not yet apply.  "In review" means an open pull request.  Then "planned" and "prompt only."  [FILL on the day: the tag of the Evaluator checks, the hand-back path, and the harness, read from the repository that morning.]

**4. One saved run and one hand-back (files)**

This is one saved run.  The input fixes the parameters, the seed, and the file hashes.  The simulator writes the results.  The Evaluator recomputes the persistence endpoint and checks the arithmetic, and returns [FILL: pass, or the list of issues].  When a required fact is missing, one request goes to the Researcher, in one batch.  If a required gap stays open, the run stops and says so; it does not guess.

**5. The history test (history report)**

We start with the 53 lynx counted in 2002 in Andújar-Cardeña.  We calibrate one number, post-dispersal mortality, on the growth to 2010.  Then we run once, with 500 trials, against the 2011 count that the model never saw.  We fixed the bounds before any run:  growth of 1.12 to 1.22, and a 2011 count of [FILL: 192.6 to 235.4, or 181.8 to 222.2, whichever the team chose].  The result:  [FILL: median growth, median 2011 count, pass or fail, stated as it came out].  We have three counts, so a pass is weak evidence, and a fail does not say which rule is wrong.

**6. The grid and its limits (Table 1, Figure 1)**

Across food levels and areas, [FILL: persistence share with 95% intervals, from the final batch].  Four limits matter most.  The model treats every food level above 4.6 per hectare the same, so it cannot tell them apart.  The cliff at 4.6 is our assumption.  Area matters only through the number of territories.  And persistence means that at month 120 a living female of breeding age holds a territory and a living male of breeding age shares her patch, not long-term viability.

**7. What stays open**

Still open:  the 2011 target, 214 or 202; the area assumption; [FILL: any decision still open on the day]; and the sources that we have not read in full (`docs/unread-sources.md`).  Everything is in the repository, with the commands to reproduce it.  Thank you.  We are glad to take questions.

## Before you start

1. Close every window that shows `.env` or a key, and turn on Do Not Disturb.
2. Open the slide PDF and the saved files of `docs/demo-plan.md` ("The fallback") in the order of the beats:  the history report, the batch files and summaries, one `results.json` with its `evaluation.json`, and the traces of the live pass.
3. Read the status tags from the repository that morning, and fill every [FILL] bracket from a saved file.
4. If a command is shown live, set the terminal font to 24 points or larger.
5. Keep the saved run and the slide PDF ready as the backup that needs no key and no network.
6. The day before (Sunday 2026-11-01), rehearse once aloud with a timer, then rehearse only the seams four times:  the last line of one speaker into the first line of the next.

## Rehearsal rules

- Read the script aloud with a timer.  About 130 words a minute is a steady pace; the script is about 450 words, so it runs near 3:30 before pauses, with room for the screen changes.
- If the run is long, cut in this order:  the second half of beat 3, the hash and snapshot detail in beat 2, then the hand-back sentences in beat 4.  Never cut the limits in beats 5 and 6.
- If a live call fails, say so and show the saved file from `docs/demo-plan.md` ("The fallback").  Do not retry in front of the audience.
- No beat depends on the API key; every live call is recorded before 2026-10-30.
- Fill every bracket from a saved file, never from memory, and say "not yet run" for anything with no file.

## To agree

Who speaks which beat; whether the slot is exactly four minutes or has a question period after it; which saved run to show in beat 4; which 2011 target to state in beat 5.

## Facts behind the numbers (for questions)

| Claim in the script | Source |
|---|---|
| Growth bounds 1.12 to 1.22 (1.17 plus or minus 0.05); observed growth (190 / 53) ^ (1 / 8) = 1.173 | `docs/history-test.md` |
| One held-out batch of 500 trials; calibration changes post-dispersal mortality only | `docs/history-test.md`; `docs/history-preregistration.md` (#62) |
| 2011 bounds 192.6 to 235.4 (for 214) or 181.8 to 222.2 (for 202), plus or minus 10% | `docs/history-test.md`; the choice is open |
| 53 lynx counted in 2002 in Andujar-Cardena | `data/history/counts.csv` |
| Food above 4.6 rabbits per hectare gives the same run; the 4.6 cliff is our assumption | `docs/model-conventions.md`; `docs/research-notes.md` (the monograph says 1.0 and 4.6 were enough, not minimums) |
| Persistence:  a living female of breeding age holding a territory and a living male of breeding age in one patch at month 120 | `docs/agent-handoffs.md` (the `settled` field) |
| Three roles, the harness, and the status tags | `docs/architecture.md`; `docs/demo-plan.md` |
| The script runs near 3:30 | about 450 words at about 130 words a minute |
