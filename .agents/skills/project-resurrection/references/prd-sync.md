# PRD alignment and pending repository synchronization

Reviewed: October 22, 2026.
Source: https://docs.google.com/document/d/1Hki-aSMezwRhHNW6Luye2z_ExSv5C_etIIxb4rqSoHc
Source revision: AHj4eMQKlkrEzU4hHf-FSYO5I2ICf_ByQSo3q9TKoeT5N4GhDiFX09FsDOcwKLE6EkjTst4f3eexqVhmJt9yLUfrTYmiKus3WD_aBDu15_A
Reviewed all four project tabs; the Strong PRD Example tab is reference material.
Repository reference inspected at the PRD review: develop at cc3b8fc.
The simulator branch was subsequently updated to that revision.

## Changes to carry into implementation

- 100 trials per experimental cell for the pilot; 500 per cell for final runs.
- Fixed seed/configuration: 3 of 3 replays identical.
- Historical target: median annual multiplicative total-population growth within
  0.05 of 1.17; held-out 2011 total count within 10%. Confirm definitions and
  calculations with Valerie before execution, never after seeing results.
- Reject 10 of 10 planted malformed handoffs before simulation; pass all three
  eval-card cases; no fourth revision.
- Compare the three-role split with one agent plus a fresh second pass. The
  detailed repo plan uses six flaws, five repetitions per case per arm, at least
  one more flaw caught per run on average and no more false alarms. No result
  has been measured yet.
- Fresh evaluator session; source/version validation before judgment; immutable
  per-round artifacts and a trace documenting the first wrong turn.
- Content-hash checks are merged in PR #9, not still awaiting review.
- Claude through LiteLLM and individual local keys is the provider proposal in
  merged PR #18. The decision document still requests both partners' agreement.
- Generated code execution follows the draft isolation plan. A directory and
  file-tree checks alone are not a sandbox; enforcement must be demonstrated.

## Preserve these boundaries

Doñana 1992–2001 is parameter evidence. Andújar–Cardeña 2002–2011 is the separate
historical comparison, with calibration through 2010 and a held-out 2011 count.
The synthetic 20-lynx initialization is separate from both. Rabbits stay a food
input in the MVP. Disease shocks are excluded. Rabbit generators/population
models and the ferret/prairie-dog portability exercise remain optional.

Valerie withdrew the PR #8 split request after merging it. Keep one task per PR,
but do not reproduce that historical split. Subsequent conversation confirmed
simulator rules; the skill body includes those later decisions. This PRD snapshot
is historical context, not a reason to revert the later user-approved rules.

## PRD issues to resolve during synchronization

- Several cells contain both revised and old text concatenated together; retain
  intended new wording without silently deleting substantive requirements.
- Broken repository URLs contain `project-resurrectionmulti-agent-system` and
  a malformed `/pull/83`; replace with verified links in the documentation pass.
- The appendix simultaneously lists explicit historical tolerances and says
  tolerances are undecided. The subsequent user conversation accepted the values
  recorded in the skill; bring the PRD wording into agreement with that decision.
- The zero-food edge case assumes extinction before month 120. A breeding-only
  cutoff does not guarantee that outcome in a finite stochastic run. Agree on a
  deterministic extinction fixture or test observed outcomes without forcing it.
- PR #3/#8 and #9 status descriptions lag GitHub. Distinguish merged contracts
  from runtime implementation, which is not established by documentation merges.
- Architecture text attributes ID/seed checks to a hash checker. Verify each
  control against its code before claiming enforcement.
- Provider fields differ by tab (proposed vs undecided); preserve proposal status
  consistently until the partners decide.

## Pending task: update the repository PRD

No dedicated repo PRD file was found in the inspected develop tree. Before
simulation integration is finalized, prepare a focused documentation PR from
current develop to create/update `docs/prd.md`, unless the team chooses another
canonical path. Re-read the latest Google PRD, synchronize all substantive
requirements, repair stale links/text, and cross-reference existing architecture,
handoff, evaluation, execution, provider, and trace docs instead of duplicating
inconsistent specifications. Record the source URL, revision, and sync date.

Keep this task separate from simulator implementation. Anastasiya has authorized
the skill PR; repository PRD synchronization remains a separate documentation
task, not completed by this skill PR. The historical PR-split request was withdrawn.
