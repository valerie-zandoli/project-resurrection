# History test pre-registration (DRAFT until the second observable is decided and the freeze items are filled)

Started 2026-10-25 by Valerie with Claude Code.  This file fixes the history test before any run, as `docs/history-test.md` requires.  **It is not in force until the blanks marked TO FILL are filled in one commit that says why, and Anastasiya agrees.**  The held-out batch has not been run, and no result has been looked at.  Code:  `simulation/history.py` (#50).

## Fixed before any run

- **Question:**  does the model, with Donana parameters, grow the 2002 Andujar-Cardena population at about the later rate, and land near the 2011 count that it never saw?
- **Starting population:**  53 animals (25 adults, 28 non-adults); adult ages 36 to 108 months; non-adult ages 0 to 35 months; cub sex ratio of the table; 12 or 13 adult females by seed; two patches.
- **Census month:**  month 0 is a December (end of the year); months 96 and 108 are Decembers.
- **Food:**  4.6 rabbits per hectare (any value at or above the spring threshold gives the same run).
- **Calibration:**  change post-dispersal annual mortality only, 0.10 to 0.50 in steps of 0.01, 100 trials per value, months 0 to 96 only; choose the value whose median growth is closest to 1.17 (a tie goes to the lower value).
- **Held-out batch:**  500 trials at the calibrated mortality, through month 108, once.  Nothing is retuned after it.
- **Seed rule:**  each trial seed is the first 8 bytes of SHA-256 of `run_seed|cell|trial`; the cell is `calibration-m<mortality>` or `heldout`.
- **Run seed:**  20261101.
- **Pass:**  both medians inside their bounds on the held-out batch:  growth 1.12 to 1.22 (1.17 plus or minus 0.05) and the 2011 count inside the bounds below.

## TO FILL after both owners decide

| Item | Options | Decision |
|---|---|---|
| 2011 target and bounds | 214, bounds 192.6 to 235.4; or 202, bounds 181.8 to 222.2 (plus or minus 10%) | **202, bounds 181.8 to 222.2**, chosen by Valerie on 2026-10-25 on source quality (the issuer's 2011 and 2016 reports give 202; no primary document gives 214); agreed by Anastasiya on 2026-10-25 (Slack, 20:36 ET, and her comment on #50).  214 (bounds 192.6 to 235.4) is reported beside the verdict and never used for pass or fail. |
| Main area and sensitivity areas | main 750 km2 (decided 2026-10-24, awaiting Anastasiya); sensitivity 500 and 1,000; proposed 264 km2 with home ranges 10 and 6.1 | **Main run:  750 km2 at the table's female home range of 10 km2** (a stand-in for the park boundary, not measured usable habitat).  **Comparison runs:  264 km2 at female home ranges of 6.1 and of 10 km2.**  The 500 and 1,000 km2 runs are dropped.  The verdict uses the 750 km2 run only, and the code refuses an arm list that starts with another arm.  Territory capacity:  74, 42, and 26 female territories.  Agreed on 2026-10-25:  recorded in #45, which Anastasiya approved and merged. |
| A second observable (territorial females, 43 in 2010 and 51 in 2011) | add, or leave out | **PROPOSED by Valerie, awaiting Anastasiya** (decision 7 of the Meet list):  add it as **report-only, for the 750 km2 run only**.  The report prints the model's median number of settled females at months 96 and 108, with the 10th and 90th percentiles, beside the census counts of 43 and 51.  It has no tolerance and no pass or fail, and we will not call it support or failure.  The 264 km2 runs hold only 42 and 26 female territories, below the census counts, so their numbers are printed marked capacity-limited and are not compared.  If Anastasiya has not answered by Wed 2026-10-28, 12:00 ET, it is left out.  The report code needs a small addition (a separate pull request) before the freeze (Thu 2026-10-29, #54). |
| Settlement retry rule | monthly, own patch first (chosen 2026-10-24, awaiting Anastasiya) | **Every month, each unsettled female of at least 18 months tries again, her current patch first and then the other, in one seeded random order per month.**  Chosen by Valerie on 2026-10-24 and recorded in `docs/model-conventions.md` by #49, which Anastasiya approved and merged on 2026-10-25.  The two sensitivity checks (own patch only, one try only) have no simulator option yet and are not part of this verdict. |

## TO FILL at the freeze, in the same commit

The freeze is Thu 2026-10-29 (#54).  Fill these four items in the commit that freezes the code, and merge this file before the run.  The run happens after the freeze and is finished by Fri 2026-10-30, 18:00 ET.

- The commit of the code that will run (hash):  TO FILL.
- The hashes of the two research files:  TO FILL (`validators/handoff_hashes.py`).
- The Python version:  TO FILL.
- The date and the name of the person who ran it:  TO FILL.

## What counts as looking

Reading any held-out result, even from another seed, before this file is complete.  Development smoke runs must use other seeds, a tiny trial count, and must not print the 2011 count.  A change after any look needs a new version of this file with the reason, and the first held-out result stays on record.
