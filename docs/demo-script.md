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

Across food levels and areas, [FILL: persistence share with 95% intervals, from the final batch].  Four limits matter most.  The model treats every food level above 4.6 per hectare the same, so it cannot tell them apart.  The cliff at 4.6 is our assumption.  Area matters only through the number of territories.  And persistence means a living breeding pair at month 120, not long-term viability.

**7. What stays open**

Still open:  the 2011 target, 214 or 202; the area assumption; [FILL: any decision still open on the day]; and several sources that we read only in abstract.  Everything is in the repository, with the commands to reproduce it.  Thank you.  We are glad to take questions.

## Rehearsal rules

- Read the script aloud with a timer.  About 130 words a minute is a steady pace; the script is about 450 words, so it runs near 3:30 before pauses, with room for the screen changes.
- If the run is long, cut in this order:  the second half of beat 3, the hash and snapshot detail in beat 2, then the hand-back sentences in beat 4.  Never cut the limits in beats 5 and 6.
- If a live call fails, say so and show the saved file from `docs/demo-plan.md` ("The fallback").  Do not retry in front of the audience.
- No beat depends on the API key; every live call is recorded before 2026-10-30.
- Fill every bracket from a saved file, never from memory, and say "not yet run" for anything with no file.

## To agree

Who speaks which beat; whether the slot is exactly four minutes or has a question period after it; which saved run to show in beat 4; which 2011 target to state in beat 5.
