# Baseline test: do three roles beat one agent? (DRAFT)

Drafted 2026-10-22 by Valerie (Evaluator owner) with Claude Code.  LaNice's lesson on multi-agent systems says to stay with one agent until it clearly breaks.  This test checks whether our split earns its cost.

## Planted flaws

Eight runs, each a copy of an otherwise valid run with one flaw:

1. births and deaths do not balance in one month;
2. a parameter outside its published range;
3. an unknown source key;
4. the trapping share added on top of the all-cause mortality (a double count);
5. the 2011 count used inside the calibration (history leakage);
6. persistence computed from the wrong endpoint;
7. a conflict named in the research notes dropped from the table (no `contradicts` entry);
8. two sources that repeat one study counted as two origins.

## Case files for flaws 7 and 8

`scripts/baseline_cases.py` builds these two cases from the three research files (the parameter table, `sources.csv`, and the evidence columns file) as three folders, `valid`, `flaw7`, and `flaw8`, plus `key.json`, the truth.  Flaw 7 sets the `contradicts` cell of one row (default `breeding_age_min`) to `none_identified` and clears the draft note that points at the conflict.  Flaw 8 adds a source that only repeats a study already in the row (default `eu_spain_report2018`, which cites Palomares et al. 2001) to the spring rabbit threshold row, gives it a new origin label, and raises the confidence to high.

Both flawed cases pass `python -m validators.parameters` with `--evidence`; this was checked on the evidence draft files on 2026-10-25.  The validator checks structure, not meaning, so only an arm that reads the sources can catch them.  Keep `key.json` from the arms until the scoring step.  Flaws 1 to 6 act on results and history files, and their case files are not built yet.

## Arms

- A:  one agent does research, simulation, and evaluation in one session.
- B:  one agent, then a second pass in a fresh session that changes nothing.
- C:  the three roles through the harness.

## Procedure

- The same eight cases, the same model, and the same prompt budget for every arm; each arm runs each case 5 times.
- Record flaws caught, false alarms, tokens, and minutes.
- Score with arm labels hidden (a script, or a person who does not know the arm).
- Arms A and B can run with hand-prepared files before the harness exists; arm C waits for the harness.

## Bar (written before any run)

Arm C must catch at least 1 more planted flaw per run than arm B on average, with no more false alarms.

## If the bar is missed

Report the counts plainly, including any case where one agent matched or beat the team.  The split is then justified only by independent review and separate permissions, and the PRD says so.

## Limits

Eight cases times five runs (40 per arm) is a small sample.  Report counts, not significance claims.  A trace that reports zero missed contradictions does not show that none were missed; only the planted flaws and the audit test for that.
