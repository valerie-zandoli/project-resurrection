# Sources not read in full, and what each one supports (PROPOSED)

Written 2026-10-24 by Valerie with Claude Code, from `data/parameters/sources.csv` and the baseline table on `develop` at `a6e8eca`.  The registry's "how read" column is our own record and has not been re-checked against the sources; re-check a row when you read its source.  Read the top row first:  the order follows how much each parameter moves the results.

| Priority | Source | How read | Parameters that cite it | Why it matters | Where to get it |
|---|---|---|---|---|---|
| 1 | `palomares2001` (Wildlife Monographs 148) | NOT READ | spring and autumn rabbit thresholds, low and medium food levels | the whole food axis | the CSIC repository lists a free PDF (3.21 MB), `digital.csic.es/handle/10261/58641`, found 2026-10-24 and not opened |
| 2 | `catsg`, `palomares2001a`, `lopezbao2014` | web page; abstract only; abstract only | `female_home_range_km2` (`catsg` also names breeding age, birth month, dispersal age, male range, diet) | the home range sets the number of territories (area divided by home range), so it drives the history test; the 10 km2 average comes from `catsg`, which names no study, and all three sources are Donana-based or abstract-level | `palomares2001a`: J Appl Ecol 38:9-18; `lopezbao2014`: J Anim Ecol 83:934-942; `catsg` is a summary and cannot be the only source |
| 3 | `ferreras1992` | repository abstract only | annual mortality (the calibration parameter), shares of deaths from trapping and traffic | mortality is the one parameter that the history test changes, and its baseline of 0.37 rests on an abstract | Biological Conservation 61:197-202 (library or JSTOR) |
| 4 | `ferreras2004` | abstract only | dispersal age, share of dispersers that settle | dispersal age 18 months is an assumption in the simulator | Behavioral Ecology 15(1):31-40 |
| 5 | `official_census_2010`, `official_census_2011`, `iberlince2017_census` | named only | none directly; they stand behind the history counts | the 2011 target (214) has a conflicting value, see below | see below |

## The 2011 count has two values

`data/history/counts.csv` holds 214 lynx for Andujar-Cardena in 2011 (`catsg`, "including 90 adults").  A copy of the 2016 census report on the Cortes de Aragon site (`bases.cortesaragon.es`, file `Informe_Censo_2016.pdf`, read 2026-10-24) gives the series for Andujar-Cardena:  total 53 in 2002, 190 in 2010, and **202 in 2011**; territorial females 43 in 2010 and 51 in 2011; occupied area ("Superficie") 264 km2 in 2010 and 282 km2 in 2011.  The report's own sums agree (Sierra Morena 2011:  202 + 18 + 4 = 224; Andalusia 224 + 86 = 310).  Two values for one count is a contradiction that the evidence table must record, and the held-out target (214, bounds 192.6 to 235.4) is Valerie's and Anastasiya's decision.  Confirm the original issuer of the report before citing it.

## Not done

- No source was read in full today except the census tables above.
- No registry row was changed; adding the official census series is a separate data pull request.
