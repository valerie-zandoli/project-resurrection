# Four-minute demonstration script (DRAFT)

Drafted 2026-10-24 by Valerie with Claude Code.  This is a first draft for Valerie and Anastasiya to rewrite in their own voices.  The presenter split and the times are proposals; nothing is agreed.  `docs/demo-plan.md` (in review, #54) holds the dates and the fallback files; this file holds the words.

Text in [FILL: ...] brackets depends on a run that has not happened yet.  Do not present a bracket as a result.

## Time budget (4:00 maximum, with about 14 seconds of slack)

The video takes about 60 seconds of the four minutes (a proposal).  Each beat includes 3 seconds for the screen change; spoken beats run at about 130 words a minute.

| Clock | Beat | On screen | Proposed speaker | Words |
|---|---|---|---|---|
| 0:00 to 0:17 | The question | slide 1 | Anastasiya | 30 |
| 0:17 to 0:39 | Three roles and the harness | architecture diagram | Anastasiya | 41 |
| 0:39 to 1:02 | What runs today | status slide | Valerie | 44 |
| 1:02 to 2:05 | Video: the scripted preview | preview slide, then the video | Valerie | 100 |
| 2:05 to 2:46 | The history test | history report | Valerie | 83 |
| 2:46 to 3:24 | The grid and its limits | Table 1 and Figure 1 | Anastasiya | 76 |
| 3:24 to 3:46 | What stays open | open-decisions list | both | 42 |

## Script

**1. The question (slide 1)**

Can a small Iberian lynx population survive for 120 months?  We built a simulation to ask, with three agents and one piece of ordinary code to run it with care.

**2. Three roles and the harness (diagram)**

The Researcher reads the sources and writes the parameters.  The Simulation Developer runs the model.  The Evaluator checks the results.  The harness, which is ordinary code, passes the files and limits revisions to three rounds.  The prompts ask; the code guarantees.

**3. What runs today (status slide)**

Every claim carries a tag.  "Tested only" means merged code with a named test that the running system does not yet apply.  [FILL on the day: the tag of the Evaluator checks, the hand-back path, and the harness, read from the repository that morning.]

**4. Video: the scripted preview (about 60 seconds, voice-over)**

scripted preview; the Researcher inspects existing tables.  The simulation and the Evaluator's code check are real; the role replies are scripted, and one live Claude pass has run separately; it is in review.  First, a planted flaw, a wrong persistence endpoint:  the code check returns revise, with the issue.  The harness cannot yet loop back to a corrected run by itself.  Then the clean run:  pass.  On 26 October we said that nothing was enforced in a live run.  Since then the code checks decided one live pass, and this video shows the same check on a saved planted flaw.

**5. The history test (history report)**

From the 53 lynx counted in 2002 in Andújar-Cardeña, we calibrate one number, post-dispersal mortality, on growth to 2010.  Then one run of 500 trials meets the 2011 count that the model never saw.  We fixed the bounds first:  growth 1.12 to 1.22; a 2011 count within 10% of 202.  The result:  [FILL: median growth, median 2011 count, pass or fail, as it came out].  With three counts, a pass is weak evidence, and a fail does not say which rule is wrong.

**6. The grid and its limits (Table 1, Figure 1)**

Across food levels and areas, [FILL: persistence share with 95% intervals, from the final batch].  Four limits matter.  Food above 4.6 per hectare is treated as one level, so the model cannot tell those apart.  The cliff at 4.6 is our assumption.  Area matters only through the number of territories.  Persistence means that at month 120 a living breeding-age female holds a territory and a living breeding-age male shares her patch; it is not long-term viability.

**7. What stays open**

Still open:  the area assumption; [FILL: any decision still open on the day]; and the sources that we have not read in full.  Everything is in the repository, with the commands to reproduce it.  Thank you.  We are glad to take questions.
## Video and slide text

The format (told by Valerie on 2026-10-26):  a four-minute maximum, slides and video, in the Sunnyside space, showing improvement over each previous presentation.  The script above was cut on 2026-10-26 to fit the video:  the video takes about 60 seconds of the four minutes (a proposal for Valerie and Anastasiya to change), and the spoken beats share the rest.

**Caption (required).**  Every screen and slide that shows the three-role preview carries the words **scripted preview; the Researcher inspects existing tables**.  The command (`python -m harness.three_role_preview`) prints them as its first and last line, so a recording of it carries them; say them aloud once in the voice-over.

**Slide text (the preview).**  Title:  "What a scripted run shows".  Lines:  "scripted preview; the Researcher inspects existing tables";  "the code check catches a planted flaw:  revise, with the issue";  "then the clean run passes";  "this preview is scripted; one live Claude pass has run (in review)".  Footer:  "Synthetic preview; historical validation not assessed."

**Video (Valerie records it on Friday 2026-10-30 after the freeze).**  (1) The caption line.  (2) The Evaluator's check on the planted flaw 6 case (#69):  `revise`, with the issue.  (3) The unflawed run:  `pass`.  The commands are in "Video commands" below (dry run on 2026-10-26; repeat them on the frozen version).  Label step 2 a planted flaw:  the harness cannot yet loop from `revise` to a corrected run by itself.  **Improvement over 26 October:**  that presentation said that nothing was enforced in a live run; since then the code checks decided one live pass (in review), and the video shows the same check on a recorded planted flaw.

## Video commands (dry run on 2026-10-26)

Run on the branch of #104 (commit `6d2fb90`, which holds #94, #103, and #104) from the repository root in the Python 3.12 environment.  Repeat every command on the frozen version before recording.  Each output folder is new:  add a take number (`-take2`) to every folder name when you record again.

1. The caption line and the clean scripted run (prints the caption first and last, then `pass`):

   ```sh
   python -m harness.three_role_preview --preview --seed 7 --months 12 --output /tmp/lynx-three-role-1
   ```

2. Build the planted-flaw cases once, before recording (`case-5` is the flaw 6 case and `case-2` is the unflawed run for `--blind-seed 1` on this commit; read `/tmp/lynx-cases-key.json` to confirm, and keep that file off the screen):

   ```sh
   python -m scripts.baseline_cases_runs --output /tmp/lynx-cases --blind-seed 1
   ```

3. The Evaluator's code check on the planted flaw 6 case (exit status 1; says `revise`, with the issue `persistence_recomputed`: `persisted is True but the final animals give False.`):

   ```sh
   python -m validators.results_checks --input /tmp/lynx-cases/case-5/input.json --results /tmp/lynx-cases/case-5/results.json --root /tmp/lynx-cases/case-5/root --output /tmp/lynx-eval-flaw6.json
   ```

4. The same check on the unflawed run (exit status 0; says `pass`, 0 issues):

   ```sh
   python -m validators.results_checks --input /tmp/lynx-cases/case-2/input.json --results /tmp/lynx-cases/case-2/results.json --root /tmp/lynx-cases/case-2/root --output /tmp/lynx-eval-clean.json
   ```

Each command ran in under a second.  The voice-over, not the commands, sets the length of the video.  Label step 3 on screen as a planted flaw.  A simulator change can change which case is flaw 6 (`docs/baseline-test.md`, Limits).

## Before you start

1. Close every window that shows `.env` or a key, and turn on Do Not Disturb.
2. Open the slide PDF and the saved files of `docs/demo-plan.md` ("The fallback") in the order of the beats:  the history report, the batch files and summaries, one `results.json` with its `evaluation.json`, and the traces of the live pass.
3. Read the status tags from the repository that morning, and fill every [FILL] bracket from a saved file.
4. If a command is shown live, set the terminal font to 24 points or larger.
5. Keep the saved run and the slide PDF ready as the backup that needs no key and no network.
6. The day before (Sunday 2026-11-01), rehearse once aloud with a timer, then rehearse only the seams four times:  the last line of one speaker into the first line of the next.

## Rehearsal rules

- Read the script aloud with a timer.  About 130 words a minute is a steady pace; the spoken beats outside the video are 316 words, which runs about 146 seconds, and the video adds 60 seconds, so the plan totals 3:46 with 14 seconds of slack.  The count includes the [FILL] brackets as written now; a longer result will add time.
- The 2026-10-26 cut already took the second half of beat 3, the hash and snapshot detail in beat 2, and the old beat 4 (one saved run and one hand-back).  If the run is still long, shorten the video voice-over (keep the caption and the two verdicts), then the sources phrase in beat 7.  Never cut the caption, or the limits in beats 5 and 6.
- If a live call fails, say so and show the saved file from `docs/demo-plan.md` ("The fallback").  Do not retry in front of the audience.
- No beat depends on the API key; every live call is recorded by Fri 2026-10-30, 18:00 ET.
- Fill every bracket from a saved file, never from memory, and say "not yet run" for anything with no file.

## To agree

Who speaks which beat; whether the slot is exactly four minutes or has a question period after it; whether the video may take about 60 seconds; which saved run, if any, to show beyond the video.

## Facts behind the numbers (for questions)

| Claim in the script | Source |
|---|---|
| Growth bounds 1.12 to 1.22 (1.17 plus or minus 0.05); observed growth (190 / 53) ^ (1 / 8) = 1.173 | `docs/history-test.md` |
| One held-out batch of 500 trials; calibration changes post-dispersal mortality only | `docs/history-test.md`; `docs/history-preregistration.md` (#62) |
| 2011 bounds 181.8 to 222.2 (202 plus or minus 10%), agreed 2026-10-25; the Cat Specialist Group's 214 is reported beside the verdict only | `docs/history-test.md`; `docs/history-preregistration.md` (#62) |
| 53 lynx counted in 2002 in Andujar-Cardena | `data/history/counts.csv` |
| Food above 4.6 rabbits per hectare gives the same run; the 4.6 cliff is our assumption | `docs/model-conventions.md`; `docs/research-notes.md` (the monograph says 1.0 and 4.6 were enough, not minimums) |
| Persistence:  a living female of breeding age holding a territory and a living male of breeding age in one patch at month 120 | `docs/agent-handoffs.md` (the `settled` field) |
| Three roles, the harness, and the status tags | `docs/architecture.md`; `docs/demo-plan.md` |
| The plan totals 3:46 | 316 spoken words outside the video at about 130 words a minute, 60 seconds of video, and 3 seconds per screen change |
