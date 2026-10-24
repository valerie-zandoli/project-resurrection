# Research notes for the Iberian lynx parameter table (DRAFT)

Drafted 2026-10-20 on branch `dev-valerie` by Valerie with Claude Code.  Nothing here is on `main` until Anastasiya reviews it by pull request.

## How to read the table

- `data/parameters/iberian_lynx_baseline.csv` uses Anastasiya's eight columns.  The file format and the `source` keys are a proposal for the validator; she decides.
- Every `source` value is a key in `data/parameters/sources.csv`, which records how each source was read (full text, abstract only, news item, or second-hand).
- In `evidence_or_assumption`, "Published" means the value or range appears in the source.  "Chosen by us" means we picked a sensitivity range; no source gives one.  "SECOND-HAND" means we have not opened the primary paper.  "ASSUMPTION" means the model needs the number and no source gives it.
- Intervals marked Wilson were computed by us from a published percentage and its n.

## Second pass (2026-10-20 evening): three results

1. **The rabbit thresholds are still second-hand.**  The 1 rabbit per hectare (autumn) and 4.6 (spring) thresholds come from Palomares et al. 2001 in Wildlife Monographs 148, as cited by the EU report.  That monograph is paywalled; only its library record was found.  The other 2001 paper (Journal of Applied Ecology 38: 9-18) uses a relative abundance index and gives no per-hectare values.  A library or JSTOR copy of the monograph is needed.
2. **Range size and food: the evidence conflicts.**  Palomares 2001 (J Appl Ecol, abstract) and the Cat Specialist Group say resident ranges are smaller where rabbits are abundant.  Palomares et al. 2005 report that a rabbit decline inside Coto del Rey did not change home range.  Lopez-Bao et al. 2014 (J Anim Ecol, abstract) found no support for territoriality flexing with food:  female overlap stayed low (median 0.08) across a wide range of rabbit density, and territoriality depended on lynx density in a nonlinear way.
3. **No yearly series for Andujar-Cardena exists in what we can read.**  We have anchor points only (below).  The Junta de Andalucia counts every year, but the yearly tables are not in the news items or the EU report.

## Proposed study population and period (decision needed from both of us)

- **Parameters:** Donana, Coto del Rey, 1992 to 2001 (palomares2005).  It is the only source with full reproduction and cub survival.
- **History test:** Andujar-Cardena (Sierra Morena) from 2002, using the anchor points in `data/history/counts.csv`:

  | Year | Individuals | Adults | Adult females | Source |
  |---|---|---|---|---|
  | 2002 | 53 | 25 | not found | eu_spain_report2018; catsg |
  | 2010 | 190 | not found | 44 | efe_2011_01 |
  | 2011 | 214 | 90 | not found | catsg |

- **Growth implied by the anchors (computed by us):**  individuals about 1.17 per year (2002 to 2010, and 2002 to 2011); adults about 1.15 per year (2002 to 2011).
- **Proposed split of data:**  calibrate on 2002 to 2010 and validate on the 2011 count (214).  Compare growth rates, not a yearly fit, and set the tolerance before any run.
- **Definitions differ across years:**  individuals, adults, and adult females are not interchangeable, so the test must use one definition at a time.
- **Provisional counts are revised later.**  Andalusia 2010 appears as 253, 279, and 275; 2002 appears as 102 and 94; 2011 appears as 298 (provisional) and 312 (final); Andalusia territorial females for 2010 appear as 66 and, by later arithmetic, 63.
- **Management helped growth:**  169 agreements covering 180,840 ha for rabbit and lynx habitat (2011), reintroductions at Guadalmellato (2009) and Guarrizas (2010) using lynx from Sierra Morena, and genetic reinforcement of Donana.  The model should be expected to match the trend only roughly.

## Species-wide counts through 2025 (added 2026-10-21)

- The official ministry censuses for 2024 and 2025 are now in `data/history/counts.csv`:  2023 had 2,021 individuals, 406 breeding (territorial) females, and 722 cubs; 2024 had 2,401, 470, and 844; 2025 had 2,663, 542, and 952.  The 2023 total is stale; date every count.
- The report says its figures are a minimum, because counting every animal is increasingly difficult.
- The eastern Sierra Morena nuclei, which include Andujar-Cardena, went from 638 individuals in 2024 to 613 in 2025 while the species total grew 10.9%.  That fits habitat saturation, but it is one year of data (our reading).
- **Reproduction sanity check (computed by us):**  litter size 3.0 times breeding probability 0.833 times survival to 3 months 0.75 gives about 1.87 cubs per breeding female.  The census reports 1.75 cubs per territorial female in 2025 (1.8 in 2024, 1.77 in 2023), with Andalusia at 1.5 and Castilla-La Mancha at 2.1.  The two agree closely, so the Donana values are a reasonable start.  Use 1.5 to 2.1 as the range for a model output check.  The census counts territorial females whether or not they bred, which lowers its figure.
- The 2002 to 2025 chart in the 2025 report has no printed values, so no yearly series was taken from it.

## How food and habitat should enter the model (revised)

- **Reproduction does not respond to rabbit density in Coto del Rey** between 4 and 55 per hectare (palomares2005; n=8 years, so low power).  One cub starved in the year with the lowest density.
- **Territories are exclusive and stable.**  Female overlap is low across the food gradient (lopezbao2014).  Breeding females need a territory.
- **Habitat saturation is a stated limit on growth.**  The director of the Junta's lynx program said that habitat with optimal rabbit densities fills up with lynx and growth then slows (Europa Press, 2011-12-13).  The same release set targets of 50 territorial females in Cardena-Andujar.
- **Proposal:** the number of female territories a patch can hold is patch area divided by female home range.  Treat home range as fixed in the baseline (supported by palomares2005 and lopezbao2014) and test a version where it shrinks as rabbits increase (supported by palomares2001a and catsg) as a sensitivity run.  Add the spring threshold (4.6 per hectare, second-hand) as the point below which territorial breeding fails.
- **Consequence:** if home range is fixed above the threshold, the medium (4.6) and high (55) food levels give the same capacity and similar persistence.  That would match the evidence and is not a bug.
- **Habitat quality independent of rabbits:**  females gave birth in hollow trees wider than 0.9 m (palomares2005 methods), so natal den count is one measurable factor.  Connectivity: catsg says lynx have difficulty crossing open areas wider than 5 km.

## Assumptions the model must make

- Whether range size depends on rabbit density (the evidence conflicts; run both versions).
- The share of cub deaths that depend on food (palomares2005 found none in range).
- Initial age and sex structure for the starting population.
- Which source of mortality to include; avoid double counting with `annual_mortality_rate_all_causes`.

## Gaps and conflicts to resolve

- No age-specific adult or juvenile survival yet.  The one all-cause rate (0.37, 1983 to 1989) comes from an abstract and is likely too high for a protected subpopulation.
- Sierra Morena demography is missing.  Candidates to read: Rodriguez and Delibes 2004 (Biological Conservation 118: 151-161) and Simon et al. 2012 (Conservation Biology 26: 731-736), both listed in the EU report.  Simon et al. probably holds a yearly Andujar-Cardena series; ask the Life Iberlince or Junta de Andalucia team if it stays paywalled.
- The MITECO census PDFs (2019 to 2021) may contain 2002 to 2021 trend data, but the links I found returned "not found".  Search the MITECO site for the current links.
- Gaona, Ferreras, and Delibes 1998 (Ecological Monographs 68: 349-370) is a viability model for Donana.  palomares2005 says its most sensitive parameters after the first were reproductive rate, cub mortality, and juvenile mortality.  Read it for parameter structure.
- Breeding age conflict: 3 years in palomares2005 versus "can breed at two years" in catsg.
- palomares2005 reports lifetime output as 11 to 19 cubs in the abstract but at least 14, 8, and 19 in the text.
- Disease, genetics, and maps are deferred by agreement.
- Survival of released lynx was 56 to 83% (WWF conference conclusions 2019); this is not in the table because the model has no releases.

## Source registry: the `origin` column (added 2026-10-22)

`origin` holds one or more stable origin IDs, separated by semicolons.  An origin ID is the registry key of the study or dataset that a source's numbers come from.  A primary study lists its own key.  A source that repeats other studies lists the key of each one; every ID has its own registry row, even when the study was named but not read (`how_read` says `NOT READ; named only`).  `unknown` means the source does not say, and it never counts as an independent origin.  The registry value is a menu of what a source reports, not a count:  `eu_spain_report2018` reports both Palomares 2001 and the 2017 census, which support different claims.  A planned `origin` column in the parameter table lists only the origins that support each row, and two sources with the same row-level origin count as one confirmation.  The rule is in `docs/handoff-decisions.md` (proposed); the validator does not apply it yet.  The IDs for the press items and for `eu_spain_report2018` come from the quality notes and are not checked against the original documents.
