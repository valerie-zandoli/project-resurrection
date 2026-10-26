# Research notes for the Iberian lynx parameter table (DRAFT)

Drafted 2026-10-20 on branch `dev-valerie` by Valerie with Claude Code.  Nothing here is on `main` until Anastasiya reviews it by pull request.

## How to read the table

- `data/parameters/iberian_lynx_baseline.csv` uses Anastasiya's eight columns.  The file format and the `source` keys are a proposal for the validator; she decides.
- Every `source` value is a key in `data/parameters/sources.csv`, which records how each source was read (full text, abstract only, news item, or second-hand).
- In `evidence_or_assumption`, "Published" means the value or range appears in the source.  "Chosen by us" means we picked a sensitivity range; no source gives one.  "SECOND-HAND" means we have not opened the primary paper.  "ASSUMPTION" means the model needs the number and no source gives it.
- Intervals marked Wilson were computed by us from a published percentage and its n.

## Second pass (2026-10-20 evening): three results

1. **The rabbit figures are now read first-hand (2026-10-24), and they are not thresholds.**  The monograph (Palomares et al. 2001, Wildlife Monographs 148; a free PDF is on `digital.csic.es`) says that 1.0 rabbit per hectare in autumn and 4.6 in spring were the lowest densities recorded and were enough to support lynx reproduction.  It says it could not determine the minimum density at which lynx fail, or the effect of density on how many females breed.  The EU report reads the two figures as needed densities; the primary source does not.  So the model rule "no breeding below 4.6" is our assumption, and food level 1 (the autumn figure) is applied as a spring density.  On 2026-10-24 only the abstract and the discussion pages were read closely.  On 2026-10-25 the methods on rabbit abundance (PDF pages 8 to 11) and the rabbit results (pages 17 to 18) were read too:  rabbits were counted by line transect (density = 0.57 x rabbits seen per km, adjusted r2 0.97, 69 samples) and by warren maps, not by pellets.  Density in Mediterranean scrubland ran from 55.1 rabbits per hectare (June 1994) to 2.0 (October 1996); within scrubland, density near the marsh edge (the Vera) was 55.1 and 41.5 in June 1994 and 1995 and 6.8 and 2.4 far from it; densities were 72 to 91% lower in 1996 than in 1994 and 1995, and on average 3.5 times higher in June than in autumn.  The rest of the monograph (including the discussion beyond the pages checked) was not read in this pass.
2. **Range size and food: the evidence conflicts.**  Palomares 2001 (J Appl Ecol; full text read 2026-10-25) and the Cat Specialist Group say resident ranges are smaller where rabbits are abundant.  The J Appl Ecol result rests on five ranges, with one female range inferred from male ranges, and its two predictors (rabbit pellets and short shrub cover) are strongly correlated (r = -0.98); one point was influential.  Palomares et al. 2005 report that a rabbit decline inside Coto del Rey did not change home range.  Lopez-Bao et al. 2014 (J Anim Ecol, abstract) found no support for territoriality flexing with food:  female overlap stayed low (median 0.08) across a wide range of rabbit density, and territoriality depended on lynx density in a nonlinear way.  The monograph (Wildlife Monographs 148) found no correlation between rabbit density and range size (P above 0.2), which agrees with palomares2005 and lopezbao2014 and disagrees with palomares2001a, a different paper by the same author.  It measured 9.5 km2 for adult females and 18.2 for adult males in Donana (1992 to 1996).

3. **A yearly series for Andujar-Cardena does exist.**  The Life+Iberlince report on the 2016 census (a copy on the Cortes de Aragon site, read 2026-10-24; the original file was not found online) gives total, territorial females, cubs, and occupied area for every year from 2002.  The years 2002 to 2011 are now in `data/history/counts.csv` with the definition "(official series)".
4. **The 2011 total has two values.**  `catsg` gives 214; the official series gives 202.  The issuer's own documents agree on 202:  the 2016 report (read in the original at iberlince.eu on 2026-10-25) and the 2011 report (`official_census_2011`, same site).  We found no primary document that gives 214, and the reason for the difference is unknown.  The series also gives 53 in 2002 and 190 in 2010, which match our other two anchors.  Which value is the held-out target is a decision for both owners, to be made before any run; both values stay in the counts file.

5. **Palomares 2001a read in full (2026-10-25).**  The paper indexes rabbits by pellets and gives one conversion:  114 pellets per m2 is about 4.6 rabbits per hectare in spring and 1.0 in autumn.  It cites an in-press paper that its reference list gives as the Wildlife Society Bulletin paper on three methods of estimating rabbit abundance (palomares2001b); we read that paper on 2026-10-25 and found no such conversion in it, so the conversion's origin is unverified.  It calls 114 a level at which lynx density may be higher because ranges shrink, and about 80 pellets per m2 the level for stable resident areas (resident sites averaged 79.7; unused sites 31.6; dispersal sites 35.3).  So the paper itself does not treat 4.6 as a breeding minimum.  We do not convert pellets to density:  see item 6.  Dispersing lynx used sites with only 1.1 to 1.4 times the pellets of unused sites, and in 48 of 96 simultaneous surveys the dispersing lynx were in vegetation patches shorter than 300 m on at least one axis; sex did not change habitat use.  The Word file is not stored in the repository (copyright); its SHA-256 is recorded in `data/parameters/sources.csv`.

6. **Palomares 2001b (Wildlife Society Bulletin 29: 578-585) read in full (2026-10-25); pellets are a poor stand-in for density in scrubland.**  In Coto del Rey from June 1994 to August 1995, line-transect density in Mediterranean scrubland ran from 13.2 rabbits per hectare (October) to 41.5 (June), and was on average 4.1 times lower in October than in April to June.  Pellet counts did not predict density when scrubland plots were included (adjusted r2 0.10, P = 0.082, n = 23); replacing scrubland plots with edge plots gave adjusted r2 0.43 (P < 0.001).  The author concludes that uncontrolled pellet counts cannot estimate abundance accurately but may approximate relative abundance, and that the choice of sampling sites decides the result.  Consequences for us:  the 114-pellet conversion in palomares2001a cannot be checked and should not be used; and the seasonal swing of about 4 times matches the gap between the monograph's 4.6 (spring) and 1.0 (autumn) figures, while our model holds density constant within a run (a stated limit).  Pages 5 and 8 were read word for word on 2026-10-25:  the regression is of pellet density on rabbit density (y = 0.890 + 1.110x; the units are not stated in the text), and Table 1's footnote says one habitat's density came from a regression formula "after Palomares et al. (in press)", which the reference list gives as the monograph (Palomares, Delibes, Revilla, Calzada, Fedriani, Wildlife Monographs).  The monograph (read 2026-10-25, methods and rabbit results) counts rabbits by line transect and warren maps, not by pellets, and its regression is rabbits seen per km to density, so the 114-pellet conversion is in neither paper and its origin is unverified (the monograph's discussion pages beyond those checked were not read).  The pages were read by eye in the browser (a scan); the PDF was not downloaded.

7. **The census reports tie two dips to rabbit disease (read 2026-10-25).**  The 2011 report says the fall in cubs in 2007 (22 from 54) came from a rabbit haemorrhagic disease outbreak in 2006, and the Andujar-Cardena total fell from 134 (2006) to 119 (2007).  The 2016 report says the total fell from 202 (2011) to 161 (2014) after a new strain (EHVb) in 2013, then recovered to 198 in 2016 after a rabbit-restocking plan, and that the disease raised the felines' home ranges and territory area (no numbers).  So the 2002 to 2011 history that our test compares against includes a disease dip, and the model has no disease; it can match the endpoints, not the path.  The 2016 report's remark on home ranges is qualitative evidence that range size rises when rabbits fall, which fits the female home range row's note that the evidence on food is mixed.

## Proposed study population and period (decision needed from both of us)

- **Parameters:** Donana, Coto del Rey, 1992 to 2001 (palomares2005).  It is the only source with full reproduction and cub survival.
- **History test:** Andujar-Cardena (Sierra Morena) from 2002, using the anchor points in `data/history/counts.csv`:

  | Year | Individuals | Adults | Adult females | Source |
  |---|---|---|---|---|
  | 2002 | 53 | 25 | not found | eu_spain_report2018; catsg |
  | 2010 | 190 | not found | 44 | efe_2011_01 |
  | 2011 | 214 (catsg) or 202 (official series) | 90 | not found | catsg; iberlince_censo2016 |

- **Growth implied by the anchors (computed by us):**  individuals about 1.17 per year (2002 to 2010, and 2002 to 2011); adults about 1.15 per year (2002 to 2011).
- **Agreed split of data:**  calibrate on 2002 to 2010 and validate on the official-series 2011 count of 202 (bounds 181.8 to 222.2).  Retain the Cat Specialist Group's 214 beside the result for comparison only; it does not determine pass or fail.  Compare growth rates, not a yearly fit, and set the tolerance before any run.
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
