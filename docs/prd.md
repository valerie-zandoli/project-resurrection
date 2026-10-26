# Project Resurrection — Product requirements

Owners: Anastasiya Glegg and Valerie Zandoli. Synchronized October 22, 2026; five passages
updated October 24, 2026 and refreshed October 25, 2026 (see the note after the source line).

Source: [Google PRD](https://docs.google.com/document/d/1Hki-aSMezwRhHNW6Luye2z_ExSv5C_etIIxb4rqSoHc).
Source revision of the full synchronization: `AHj4eMQFw1S02f_cz2RAmPjNIUGZjdxBgVr9yfwvIUeqjV0182-oekqMJ6pjSt9M9Z1TkZ-PSXMXwy_IPbh2hDLf_BkEqi7xdA9WNESaunU`.

Targeted update, October 24, 2026:  five passages below were changed to match the Google PRD at
revision `AHj4eMTnw-BAwiilLc4dSN01v_lda1lYIRWesZM9B--MI7lOvHCY27rcZKAtluzwq2EyoD7TGFX6jIRN8qh02SOCYi_0GGZG7HUMTlEyYKs`
(the usable area of the history run, the settlement retry rule, the status of PR #32, and the
simulator preview in PR #40).  The other sections were not compared again and are as synchronized
on October 22.

Refreshed October 25, 2026:  the area passages and the retry-rule passage now record what both owners
agreed on October 25 (#45 and #49), and the held-out 2011 target now reads 202 (#62).  The Google PRD
was not read again for this refresh; where it still gives other values, it is out of date, and its
owner is to update it.

This specification consolidates all four project tabs: **PRD: Net new build**,
**PRD: New feature**, **Agent PRD: Net new build**, and **Agent PRD: New feature**.
Strong PRD Example is reference material. Requirements are not evidence that the
described runtime exists. Proposals below remain proposals until agreed.
The persistence section also records the partners' later October 22 approval
of territory settlement and the subsequent contract update in PR #39.

## Problem and users

Explore how rabbit availability and usable habitat area affect Iberian lynx
population persistence. The conservation motivation is the species' historical
risk of extinction. This is an educational research prototype for learning and
hypothesis exploration, not a validated conservation forecast or operational
recommendation. No commercial demand or measured time-saving benefit has been
established. The initial build budget is 12–16 hours.

Researchers are the primary users. They need configurable scenarios, sourced
parameters with units/ranges/assumptions, reproducible histories, uncertainty
estimates, and independent evaluation. Secondary users are students, wildlife
enthusiasts, and conservation staff. They need accessible explanations, graphs,
and limitations to understand findings and explore research questions.

## Scope and ownership

Researcher → Simulation Developer → Evaluator. Ordinary Python code runs the
numerical model. The harness validates and routes artifacts, tracks revisions, and
reports pass or stop. Claude Code and Codex help the teammates develop the
repository; they are not the runtime role agents.

| Work | Owner |
| --- | --- |
| Researcher, parameter evidence, source registry | Valerie |
| Simulation Developer and integration | Anastasiya |
| Evaluator and historical test | Valerie |
| Parameter validator and handoff examples | Anastasiya |
| Shared contracts, harness, presentation | Both |

Pairing was confirmed for October 22, 2026, 16:00–18:00 ET. Git workflow:
task branch → `develop` → `main`, through reviewed pull requests.

The MVP tracks individual lynx. Rabbit density is a fixed food input per run.
Individual rabbits, viruses, disease shocks, genetics, detailed maps, a polished
dashboard, deployment, and commercial delivery are outside the MVP. Command-line
execution and inspectable artifacts come before an interface.

### Optional extensions

Attempt only after the core lynx workflow, tests, and required deliverables are
complete and time remains. Agree assumptions/interfaces first.

1. Simple food generator: seeded monthly rabbit densities with optional
   seasonality. Rough implementation/integration estimate: 1–2 hours after rules
   are agreed; research is additional. Label outputs synthetic.
2. Rabbit population model: counts change through births, deaths, and predation,
   then convert to density using area. Rough estimate: 4–8 hours after rules are
   agreed; research is additional. This is an alternative extension, not a
   commitment to implement both.
3. Black-footed ferret/prairie-dog portability: a new sourced parameter table,
   no model-code change, and the same report checks. If species-specific code
   changes are needed, report that limitation rather than claiming success.

## Agreed synthetic experiment

| Setting | Requirement |
| --- | --- |
| Initial population | 10 females and 10 males; five of each sex per patch |
| Starting ages | Seeded whole-month draws from 36–96 months |
| Duration | 120 monthly transitions after initialization |
| Food | 1, 4.6, or 55 rabbits/ha, constant within each run |
| Usable area | Two patches, each 50 km² or each 100 km² |
| Habitat factor | `habitat_quality = 1.0` in both area conditions |
| Grid | Three food levels × two area conditions |
| Trials | 100 per cell for the pilot; 500 per cell for final runs |
| Outcomes | Endpoint persistence, final population, time to extinction |

Record configuration/seeds. Do not mix pilot and final outcomes. Extinction
time is empty when extinction has not occurred, rather than 120.

### Model rules

- March breeding requires food **at or above** the spring threshold of 4.6
  rabbits/ha and the agreed age, territory, and male-availability conditions.
  The threshold is second-hand evidence. The autumn threshold is unused with
  constant density. Threshold sensitivities: 3.0, 4.6, and 6.0 rabbits/ha.
- Medium/high outcomes may be similar: the cited evidence reports no reproduction
  effect over 4–55 rabbits/ha. Similar outcomes alone are not a bug.
- Female capacity is `floor(usable patch area / home range)`. Baseline home
  range is 10 km²; sensitivity spans 4–30 km². Call the treatment **usable habitat
  area**, not habitat quality. Five starting females fill a 50 km² patch;
  recruitment there requires a later vacancy.
- Unsettled females stay alive under all-cause mortality. The published 0.5
  settlement fraction checks outputs; it is not a second probability gate.
- Adult males may cross to the other patch once per month with probability 0.10
  (assumption), consume no female slots, and must share a patch with an eligible
  female for breeding.
- Derive conditional monthly cub survival from cumulative survival of 0.75 at
  3 months, 0.69 at 10 months, and 0.57 at assumed dispersal age 18 months.
  The points have different sample sizes. The final eight-month interval is an
  assumption; rounded monthly values are not independent measurements.
- Post-dispersal annual mortality has baseline 0.37 and sensitivity 0.10–0.50.
  Monthly survival is `(1 - active annual mortality)^(1/12)`. The older
  1983–1989 abstract may overstate protected-population mortality. Trapping/road
  shares are already within all-cause mortality; do not add them again.
- Keep baselines configurable for sensitivity and historical calibration.

### Persistence: agreed October 22, 2026

At month 120, persistence requires a living breeding-age female holding a
territory and a living breeding-age male in the same patch. Food availability
is excluded from endpoint eligibility and affects reproduction separately.
Report births in the final 12 months alongside persistence. This endpoint does
not establish long-term viability.

Every final animal has a boolean `settled`. Starting females hold five territories
per patch; young/unsettled females are false until dispersal and settlement.
Males are false and use no female territory slots; persistence ignores that field
for males. A female retains her territory while alive unless an agreed movement
rule changes it. Death frees the slot and sets the value to false.

[PR #39](https://github.com/valerie-zandoli/project-resurrection/pull/39) supplies
results contract version 2.0, the required field, sample states, and structural
tests. Old results without the field must not fall back to the weaker pair-only
definition. Runtime settlement/capacity logic and Evaluator recomputation still
need implementation. This PRD does not claim they exist.

## Separate historical comparison

Keep Doñana, Coto del Rey, 1992–2001 biological evidence separate from the
Andújar–Cardeña, 2002–2011 population comparison and the synthetic 20-lynx start.
Applying Doñana biology to Andújar–Cardeña is a transfer assumption.

The background figure of 62 **mature** lynx species-wide in 2001 is neither a
local total nor a starting count ([IUCN background](https://iucn.org/news/202407/recovery-iberian-lynx-conservation-success-spain)).

Historical anchors: 53 total individuals in 2002 (25 adults), 190 in 2010
(44 adult females), and held-out 214 in 2011 (90 adults). Calibrate only
post-dispersal annual mortality within 0.10–0.50 using 2002–2010.

Both owners accepted these tolerances on October 22, 2026:

- Median annual multiplicative growth of total individuals: 1.12–1.22
  (1.17 ± 0.05).
- Median held-out 2011 count: 192.6–235.4 (214 ± 10%).

Never change tolerances or retune after viewing the holdout. Sparse counts make
a pass weak evidence. Rough growth arithmetic is not a simulation result.

The procedure from PR #32 (merged):

- Fix census month, starting age/sex structure, trial count, and seeds before
  execution. Counts of 25 adults and 28 non-adults do not establish ages/sexes;
  proposed draws remain assumptions.
- Forty-four adult females do not establish 44 occupied territories or a minimum
  of 440 km². Usable area: the Andújar–Cardeña area is not sourced, so the
  primary run uses 750 km² as a stand-in for the park boundary (a labeled
  assumption, not measured usable habitat), with comparison runs at 264 km²
  (the 2010 occupied area) at female home ranges of 6.1 and 10 km², and the
  verdict on the 750 km² run only; both owners agreed on October 25, 2026 (#45).
- After calibration, freeze settings and evaluate one predefined ensemble
  through 2011. “Once” means one held-out batch, not one stochastic trial.
- Report medians, 10th–90th percentiles, trial count, extinct share, and the
  census-date, initialization, transfer, and sparse-data limitations.

## Validated experiment handoffs

Users must validate inputs before execution, receive file/field/run diagnostics,
inspect monthly histories/final states, replay runs, and get independent
evaluation. Numerical accounting and biology require more than JSON shapes.

| Handoff | Artifact | Context |
| --- | --- | --- |
| Researcher → Developer | `input.json` | Parameter/source paths and hashes, configuration, seed, run identity |
| Developer → Evaluator | `results.json` | Configuration, matching hashes, monthly history, final states, provenance |
| Evaluator → Developer | `evaluation.json` | Checks, issues/codes, requested changes, round, historical validation |

`data_kind` labels `sample` fixtures versus `simulation` outputs, not scientific
confidence. `historical_validation` belongs in `evaluation.json` and stays
`not_assessed` until the separately agreed test runs. See [handoff
contracts](agent-handoffs.md) and `schemas/` for implemented shapes.

The validator currently requires exactly eight parameter columns. Planned
additions are `confidence`, `confidence_reason`, `contradicts`, and claim-specific
`origin`. Adopt them only with a reviewed validator/contract migration. PR #35
is an evidence-label draft, not an implemented migration. Registry origins are
a menu; row origins support the specific claim. Unknown provenance never counts
as independent support. See [research notes](research-notes.md) and [handoff
decisions](handoff-decisions.md).

Runtime checks must cover run/seed/configuration/round consistency, contiguous
months, unique animal/patch IDs, valid patch references, final counts,
persistence, and population accounting. History includes month 0 through the
endpoint; initial event counts are zero. The harness computes hashes from actual
input files and preserves them through handoffs. Hash helpers check content
consistency, not scientific correctness or all identity/accounting relationships.

## Bounded revision harness

Round 0 is the initial attempt; developer revisions are 1–3. The Evaluator
returns `pass`, `revise`, or `stop` with actionable issues. Unresolved round-3
issues produce a stop report for both owners; never execute round 4. Preserve
per-round artifacts, configuration/seed, and recorded round. A fresh Evaluator
session independently reviews evidence, code, results, and conclusions.

Each case gets one batched Researcher clarification round, shared by Developer
and Evaluator and separate from developer revisions. Requests name the parameter,
required/optional status, reason, and resolution needed. Low confidence alone
does not block an approved provisional assumption. Resolution may correct units,
locate existing evidence, record agreed conflict treatment, or document a
human-approved assumption. New independent support is required only when that is
the actual gap. Code checks structure/references; the Evaluator judges scientific
resolution, not a page identifier.

Stop/report if a required gap remains after clarification or a new required gap
appears. Optional gaps remain disclosed limitations. Deliberately revised
research starts a fresh validated run without resetting the case clarification
budget. Reject schema mismatches, stale artifacts, killed runs, and unresolved
round-3 issues without transient retry. Retry only the failures allowed by
[handoff decisions](handoff-decisions.md); never silently drop failed trials.

The harness must enforce controls in code; helpers alone are not a complete
runtime demonstration. Treat source text/agent output as untrusted data. Ignore
instructions embedded in evidence to bypass validation. Never invent evidence,
citations, completed tool calls, results, or historical fits.

## Acceptance and evaluation

| Requirement | Target |
| --- | --- |
| Complete workflow | One inspectable end-to-end workflow; all required checks pass |
| Reproducibility | Identical results in 3 of 3 fixed-configuration/seed replays |
| Accounting | Births, deaths, population balance in all 120 transitions |
| Revision bound | Normal/edge/adversarial routing passes; no fourth revision |
| Revision identity | Scripted run/seed/round checks pass in 10 of 10 cases |
| Invalid handoffs | Reject 10 of 10 planted malformed artifacts before simulation |
| Existing checks | All current tests pass; no skipped required contract checks |
| History | Separate agreed initialization/procedure and fixed tolerances above |

Required eval cases:

1. Valid sourced synthetic inputs produce consistent histories/final states and
   evaluator findings, without claiming historical validation.
2. Zero food produces zero births under the breeding-only rule. Compute actual
   persistence under the agreed definition; do not force finite-time extinction
   or `persisted=false`. Report extinction time only when all animals die. Use a
   separate controlled fixture when guaranteed extinction is needed.
3. Invalid references, malformed output, mismatched run IDs, and instructions to
   bypass checks are rejected with diagnostics. Never substitute another run's
   artifact. Unresolved round-3 issues stop/report.

Compare three roles with one agent plus a fresh second pass. The planned target
is at least one extra planted flaw caught per run on average over five runs;
follow [the baseline plan](baseline-test.md) for cases and false-alarm checks.
No comparative outcome has been measured. Traces should make the first wrong
step inspectable. Test counts are commit-specific snapshots, not scientific
validation or fixed product targets.

## Execution and implementation status

Generated code needs isolation, read-only inputs, preserved artifacts, a scrubbed
environment, and time/memory limits. A directory alone is not a sandbox. Runtime
tools must not contact people, publish, merge, or take conservation actions.
Preserve sources and redact secrets from logs.

Parameter validation, schemas/examples, content-hash helpers, and automated
checks exist. Numerical simulation (a first synthetic preview was merged in PR #40
on October 24, 2026; no experiment has been run), the complete harness, runtime role agents,
and end-to-end enforcement remain pending at synchronization. Test passes are
not runtime results. Claude through LiteLLM with personal locally stored keys is
the provider proposal; a direct-provider key check does not prove full integration.

Detailed plans: [architecture](architecture.md), [evaluation](eval-plan.md),
[execution isolation](execution-sandbox.md), [provider](runtime-provider.md), and
[traces](trace-plan.md). If old fixtures/design notes differ from later agreed
settings here (such as all animals starting at 36 months), flag the mismatch and
update contracts through review; do not silently revert approved rules.

## Decisions still pending

PR #33 proposes survival → aging → settlement → male movement → March births →
recording; uniform litter sizes 2–4; and Wilson intervals plus population and
extinction summaries. These conventions are not yet agreed. Before experiments:

- Implement the agreed persistence/settled contract and independent runtime checks.
- Agree monthly ordering, litter sampling, historical initialization,
  observation/ensemble procedure, seed derivation, and aggregation. The usable
  area of the history run is the exception: both owners agreed on October 25,
  2026 (#45) to use 750 km² as a labeled stand-in for the park boundary, with
  comparison runs at 264 km² and female home ranges of 6.1 and 10 km².
- Settlement retries: Valerie chose on October 24, 2026 that every month each
  unsettled female of at least 18 months retries, her current patch first and
  then the other, in one seeded random order per month; Anastasiya has not yet
  confirmed it. Two other rules (own patch only, one try only) run as
  sensitivity checks, reported apart from the main grid.
- Align crash handling with transient retry rules; define incomplete cells and
  denominators before running.
- Finalize provider, execution limits/isolation, trace retention, and the shared
  state writer wherever component plans still mark them proposed.

This documentation sync does not implement conventions, migrate schemas, edit
parameter data, accept pending scientific proposals, or merge their PRs.
