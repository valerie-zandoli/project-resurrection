# History test pre-registration (DRAFT until the two open decisions are made)

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
| 2011 target and bounds | 214, bounds 192.6 to 235.4; or 202, bounds 181.8 to 222.2 (plus or minus 10%) | **202, bounds 181.8 to 222.2**, chosen by Valerie on 2026-10-25 on source quality (the issuer's 2011 and 2016 reports give 202; no primary document gives 214); awaiting Anastasiya.  214 (bounds 192.6 to 235.4) is reported beside the verdict and never used for pass or fail. |
| Main area and sensitivity areas | main 750 km2 (decided 2026-10-24, awaiting Anastasiya); sensitivity 500 and 1,000; proposed 264 km2 with home ranges 10 and 6.1 | TO FILL |
| A second observable (territorial females, 43 in 2010 and 51 in 2011) | add, or leave out | TO FILL |
| Settlement retry rule | monthly, own patch first (chosen 2026-10-24, awaiting Anastasiya) | TO FILL (agreement) |

## TO FILL at the freeze, in the same commit

- The commit of the code that will run (hash):  TO FILL.
- The hashes of the two research files:  TO FILL (`validators/handoff_hashes.py`).
- The Python version:  TO FILL.
- The date and the name of the person who ran it:  TO FILL.

## What counts as looking

Reading any held-out result, even from another seed, before this file is complete.  Development smoke runs must use other seeds, a tiny trial count, and must not print the 2011 count.  A change after any look needs a new version of this file with the reason, and the first held-out result stays on record.
