---
name: project-resurrection
description: Build and integrate Project Resurrection's Iberian lynx research, simulation, and evaluation workflow using its existing CSV/JSON contracts and bounded revision harness. Use for implementation in this project, not unrelated multi-agent systems.
---

# Project Resurrection

Repository skill for Anastasiya and Valerie, available as `$project-resurrection`.
Follow it alongside AGENTS.md and the user’s current instructions. It does not
authorize unrelated implementation, external messages, publication, or merges.

## PRD alignment

Read [references/prd-sync.md](references/prd-sync.md) before implementation or
updating repository documentation. It records the Google PRD revision reviewed
on October 22, 2026, new requirements, unresolved contradictions, and the pending
repository PRD synchronization task. Re-read the live PRD for later edits.
Do not equate a merged proposal document with agreement on every open decision.

## Purpose and scope

Support endangered-species conservation research by exploring how rabbit food
availability and usable habitat affect simulated Iberian lynx persistence.
Researchers are primary users; students, wildlife enthusiasts, and conservation
staff are secondary users. Describe findings as exploratory model results, not
validated conservation recommendations or demonstrated improvements in wildlife.

The MVP models individual lynx in two habitat patches. Each lynx has a stable ID,
sex, age, patch, and alive/dead status. Rabbits are an environmental density input
in rabbits per hectare, not individual animals. Include monthly aging/survival,
seasonal reproduction, territory settlement, and simple movement once their
rules are agreed. The numerical model is ordinary reproducible Python code.

## Inspect before changing

Read `AGENTS.md`, `README.md`, current schemas, examples, and relevant validators.
Use the actual current repository state; never assume a merged PR is already in
the checkout. The repository is `valerie-zandoli/project-resurrection`.

Anastasiya's task branch is `simulator`. Keep implementation on that branch when
appropriate. Follow current repository rules: task branch → reviewed PR into
`develop` → reviewed PR into `main`. Do not recreate the removed remote
`dev-anastasiya` branch or merge PRs without explicit authorization. Preserve
local work when syncing. A preview-only request leaves the draft uncommitted and
unpushed, even when the normal workflow calls for commits and PRs.

Valerie withdrew the request to split PR #8 after merging it. Do not recreate
the split or duplicate its changes. Continue with one focused task per PR.

Limit edits to the requested component. Do not replace shared contracts or
Valerie's research to make implementation easier. Explain needed contract changes
and make them reviewable before dependent code relies on them.

## Roles and ownership

- Valerie: Researcher, Evaluator, and baseline history test.
- Anastasiya: Simulation Developer, integration, and parameter validator.
- Together: handoff agreements, harness, and presentation.

The runtime workflow is Researcher → Simulation Developer → Evaluator, with
revision requests returning to the developer. Code manages the handoffs; a
coordinator AI is optional. Coding assistants used by the teammates are distinct
from runtime role agents, and simulated animals are distinct from both.

## Keep evidence, historical checks, and synthetic runs distinct

- Biological parameter evidence: Doñana, Coto del Rey, 1992–2001, particularly
  reproduction and cub survival.
- Separate historical comparison: Andújar–Cardeña, 2002–2011; calibration uses 2002–2010 and a held-out 2011 count. Transferring Doñana
  parameters is an explicit assumption. The agreed target is median annual
  multiplicative growth within 0.05 of 1.17 (1.12–1.22) and the held-out 2011
  total count within 10%. Confirm the precise calculation, initialization and
  observation definitions before runs. These are acceptance targets, not
  achieved results; never tune them after observing held-out outcomes.
- Synthetic starting population: 10 females and 10 males, five of each per
  patch. Sample whole-month ages uniformly from 36–96 months with the run seed;
  this distribution is an explicit synthetic initialization assumption.
- The species-wide estimate of 62 mature lynx in 2001 is background context, not
  a local population count or the synthetic model's starting count.

Do not use later census data as evidence about earlier food conditions. Keep
later conservation-status changes outside the historical comparison.

## Agreed simulator rules and remaining implementation choices

Run 120 monthly steps over three food levels (1, 4.6, 55 rabbits/hectare) by two
usable-area conditions (two 50 km² patches versus two 100 km² patches). Run 100
trials per cell for the pilot and 500 for final experiments. Preserve seeds and
require identical results in 3 of 3 fixed-seed replays. Record endpoint persistence,
final population, and time to extinction; use null/not extinct during the run
for a surviving population rather than inventing an extinction time at month 120.

Breeding happens in March at or above 4.6 rabbits/hectare, subject to age, territory,
and eligible-male requirements. Keep density constant within a run; do not use the
autumn threshold. Test thresholds 3.0, 4.6, and 6.0 separately. The spring threshold
is second-hand evidence. Matching medium/high outcomes under this rule are valid.

Compute conditional monthly cub survival from cumulative values 0.75 at 3 months,
0.69 at 10 months, and 0.57 at dispersal. Use full-precision ratios over interval
lengths rather than rounded monthly constants. An 18-month dispersal age makes
the final interval eight months; this interval and the differing study sample
sizes are explicit caveats. After dispersal, use annual mortality 0.37, with
monthly survival (1 - mortality) ** (1/12), and sensitivity range 0.10–0.50.
The mortality evidence is an older 1983–1989 abstract and may overstate protected
population mortality. Never add trapping/road shares on top of all-cause mortality.

Use the factor name usable habitat area. Keep schema field habitat_quality=1.0
in both conditions. Female capacity is floor(usable area / 10 km²). Five starting
females fill each 50 km² patch; recruits cannot settle until a vacancy exists.
Test female home range 4–30 km² separately. Settlement succeeds with a free slot;
unsettled females remain alive under all-cause mortality. The published 0.5
settlement fraction is an output comparison, not an additional probability gate.
Adult males may cross to the other patch once per month with probability 0.10;
this is an agreed assumption, not a measured rate. They use no female slots;
breeding requires an eligible male in the same patch.

Historical calibration changes only post-dispersal annual mortality within
0.10–0.50, using 2002–2010; hold out 2011. Target median annual total-individual
growth 1.17 ± 0.05 and the 2011 total 202 ± 10% (181.8–222.2), as approved
on October 25 before any run; report 214 as the alternative source value only.
Do not claim strong validation
from these few anchors. Rough growth estimates at mortality 0.37 and 0.20 are
preliminary calculations, not executed simulation findings.

The agreed endpoint requires a living breeding-age female holding a territory
and a living breeding-age male in the same patch. Food affects reproduction
separately and is excluded from endpoint eligibility; report births in the final
12 months alongside persistence. The simulator and independent result checks
implement this rule. It does not establish long-term viability.
Document monthly event order, litter-size sampling, historical initial age/sex
structure, and aggregation/selection procedure before experiments. Do not fill
these details with unsupported biological claims. Amend contracts through review
if mixed ages or new outputs cannot be represented by their current fields.

## Existing handoffs and provenance

Reuse `docs/agent-handoffs.md`, `schemas/`, and `examples/handoffs/`.
Research arrives as `data/parameters/iberian_lynx_baseline.csv` and `sources.csv`.
The eight parameter fields are:
`name,baseline,low,high,units,area_age_group,source,evidence_or_assumption`.
Validate finite numbers, low ≤ baseline ≤ high, required fields, unique names,
and semicolon-separated source references with `validators/parameters.py`.
Structural acceptance does not establish biological correctness.

Evidence labels live in the separate `evidence_columns_DRAFT.csv` sidecar; the
parameter table keeps its eight-column contract. Evidence validation/gating,
snapshotting, and a separate batched clarification helper are implemented.
Inspect current entrypoints before claiming a helper is wired into a runtime
clarification loop. Preserve approved labels, reference syntax, and failure rules.
Count underlying evidence per claim rather than all studies mentioned in a report.
Human audits and two additional planted flaws also remain planned work.

Runtime JSON contracts carry configuration, run ID, seed, revision round,
results, and evaluator findings. Monthly history runs from month 0 through the
endpoint; initial event counts are zero. Population balances births minus deaths;
movement does not change the total. Final states include every created animal,
with dead animals retaining their age/patch at death.

Use the merged `validators/handoff_hashes.py` and current schemas rather than a
new hashing convention. Inputs carry parameter/source SHA-256 values, results
preserve them in config, and evaluations carry them as specified. Normalize line
endings consistently. Verify file versions before execution and across handoffs.
A deliberate research-file change starts a fresh run with new ID and hashes.
All-zero fixture hashes are placeholders, never real provenance.

Keep `data_kind: sample` for hand-authored fixtures. Keep historical validation
`not_assessed` until the separately agreed historical comparison has actually run.

## Harness and generated-code execution

Initial attempt is round 0; allow at most revisions 1–3. A pass requires successful
required checks and no unresolved issues. Fixable issues return structured revision
requests. Unresolved issues at round 3 produce stop and a report for both owners;
no fourth revision. Bound transient tool retries separately from revisions.
External delivery of a report requires user authorization.

Read `docs/execution-sandbox.md` when present before live generated-code execution.
It is a draft plan, not proof that sandboxing exists. The chosen limits and real
isolation mechanism need Anastasiya's agreement. A working directory, isolated
Python flag, import scan, read-only file mode, or after-the-fact file scan alone
cannot contain hostile generated code. Until genuine isolation is implemented,
follow its human-code-review requirement and do not claim sandbox enforcement.
Keep model credentials out of the numerical child process and preserve per-round
artifacts and diagnostics. The opt-in runtime uses Claude through LiteLLM,
with a separate personal key per partner stored in local ignored `.env` files.
Read `docs/live-workflow.md` for implemented commands and saved integration
evidence; retain unresolved policy decisions in `docs/runtime-provider.md`.
Inspect the configured model and verify current official documentation before
changing API integration or making availability claims.
Never copy one-time key links or secrets into chat, traces, Slack, Docs, or Git.
A coding-tool subscription does not establish runtime API access.

## Build and evaluate in small steps

First milestone: one reproducible 12-month synthetic run reading validated inputs
and returning schema-valid, semantically consistent results. Start with explicit
fixtures or assumptions where needed; do not claim a complete live agent workflow
until actual role calls and harness execution work.

Use Python 3.12 and the repository virtual environment. Run `python -m pytest`
with the contract dependencies installed; skipped required checks are not passes.
Test fixed-seed replay, accounting, births/deaths/movement boundaries, source hashes,
invalid inputs, and revision termination as those components are implemented.

Read `docs/eval-plan.md` and `docs/baseline-test.md` when implementing evaluation.
Preserve their draft status and agree on expected outputs before runs. The PRD
requires all required checks, all three eval-card cases, and 10/10 malformed
handoffs rejected before simulation. Evaluator assessment uses a fresh session.
For the three-role versus single-agent comparison, follow the existing plan:
six planted flaws, five repetitions per case per arm, including a single agent
with a fresh second pass as the comparator; at least one additional flaw caught
per run on average with no more false alarms. Define the aggregation before
running and do not reduce the requirement to five total runs. Compare
normal, edge, and adversarial cases, report actual misses, and do not claim the
three-role system beats a single agent before that comparison runs. Flag any
inconsistent draft expectation for joint resolution: for example, zero food does
not guarantee extinction by a finite endpoint under a breeding-only food rule.

Keep the evaluator independent: it inspects evidence, code, configuration, and
actual output, not only the developer's self-report. Distinguish model verification
from historical validation and from evidence of real-world conservation value.

## Trace and enforcement requirements

Read `docs/architecture.md` and `docs/trace-plan.md` when implementing the harness.
The critical handoff is the parameter table plus source registry, versioned by
content hashes. Make shared-state writer and hash-computation ownership explicit;
the architecture document still lists these as open decisions. Tag each control
as enforced by CODE, requested by PROMPT, or checked by human/evaluator review.
Do not claim a hash comparator also checks run ID, seed, or round unless the
implementation actually does so. Source-key validation does not neutralize prompt
injection inside an otherwise valid source.

Record step/role, prompt version, input identities, model messages, tool requests,
result summaries, validator verdict, evaluation status, round, and truncation in
a per-run trace. Redact secrets and private data before persistence; retaining
truncation details never authorizes retaining credentials. Trace location and
retention still need agreement. Preserve immutable round artifacts. Diagnose the
first wrong turn and classify it as prompt, harness, or tool failure; record the
regression and its catching test with the fix. Human review follows the output.

## Optional work only after the lynx MVP

- Simple food generator: synthetic monthly density with seasonal variation and
  seeded randomness; no claim to reconstruct missing historical observations.
- Rabbit population model: births, deaths, and lynx predation; agree on biological
  rules and contracts before expanding the scope.
- Black-footed ferret and prairie dog: try the same model with a new sourced
  parameter table only if the lynx build leaves time. Portability passes only if
  model code stays unchanged and the report passes equivalent checks.

Disease shocks, virus transmission, genetics, detailed maps, and a polished
website are outside the first build unless the user explicitly changes scope.

## Delivery

State what works, test evidence, assumptions, remaining decisions, and limitations.
Use a small reviewed PR into `develop` when authorized. Never merge, send messages,
or publish solely because this skill describes a workflow. For preview-only work,
provide the local file and summary and wait for the user's feedback.
