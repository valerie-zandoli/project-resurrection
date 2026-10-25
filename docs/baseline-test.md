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

## Case files for flaws 1 to 6

`scripts/baseline_cases_runs.py` plants flaws 1 to 6 in copies of one valid, real simulator run and writes one folder per case (`valid`, `flaw1` to `flaw6`), each with an `input.json`, a `results.json` (not for flaws 2 and 3, which stop before any run), and a `root/` folder with the research files, plus a `key.json` with the truth.  Flaw 5 needs a history report from a real run (`--history-report`); without one it is marked "not built".  Flaws 7 and 8 live in the research files and are built by `scripts/baseline_cases.py`.

What the code reported when the cases were built (seed 3, 24 months, food 4.6, area 50):

| Flaw | Plant | What the code reports |
|---|---|---|
| 1 | one month reports one extra death | `population_accounting` and `final_counts` fail; status `revise` |
| 2 | input overrides mortality to 0.80 (published range 0.10 to 0.50) | the input schema rejects it and the simulator refuses to run |
| 3 | a table row cites the unknown source `no_such_source` | `validators.parameters` rejects it before any run, and the simulator refuses; the hashes are current, so the hash check is not what stops it |
| 4 | mortality 0.43 = all-cause 0.37 plus the road-traffic share (the table says shares are already inside the all-cause rate) | all 12 checks pass |
| 5 | a history report that says it calibrated on 108 months and the 2011 count | nothing reads a history report yet |
| 6 | `persisted` is True from the pair-only endpoint in a run where the agreed endpoint is False | `persistence_recomputed` fails; status `revise` |

So code catches four of the six (1, 2, 3, 6), and each is caught at the stage the harness plan expects.  Flaws 4 and 5 pass every code check:  only an arm that reads the table's notes (flaw 4) or the report's calibration section (flaw 5) can catch them, with flaws 7 and 8.  Those four are where the three-role split can earn its cost over one agent, so the arm comparison should report them apart from the four that code catches.  A check that reads a history report (calibration months, calibration target, one held-out run) would close flaw 5 in code; it is not built.

Limits:  the plants are synthetic and small; the flaw 6 run comes from a search over seeds for a run where the two endpoints differ (seed 6, 24 months, food 1.0 on the current simulator), so a simulator change can change the case; the history report in a case folder is a smoke-test report (3 trials), never a result.
