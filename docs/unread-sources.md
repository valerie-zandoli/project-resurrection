# Sources read and not read in full, and what each one supports (PROPOSED)

Written 2026-10-24 by Valerie with Claude Code, from `data/parameters/sources.csv` and the baseline table on `develop` at `a6e8eca`; updated 2026-10-25 after the full-text readings that #57, #66, and #68 record.  The registry's "how read" column is our own record and has not been re-checked against the sources; re-check a row when you read its source.  The order follows how much each parameter moves the results.

| Priority | Source | Status on 2026-10-25 | Parameters that cite it | Why it matters | Where to get it |
|---|---|---|---|---|---|
| 1 | `palomares2001` (Wildlife Monographs 148) | READ IN FULL (2026-10-24 and 2026-10-25; scanned PDF, read by eye; the cover, the photographs, and the rotated vegetation table were not read) | spring and autumn rabbit thresholds, low and medium food levels | the whole food axis:  by our reading of its Figure 13, 1.0 (autumn) and 4.6 (spring) per hectare are home-range averages of 1996 and levels that were enough; the study says it could not determine how density affects breeding | `digital.csic.es/handle/10261/58641` |
| 2 | `catsg` | STILL A WEB PAGE ONLY (names no study) | `female_home_range_km2` (also breeding age, birth month, dispersal age, male range, diet) | the 10 km2 average comes from `catsg`; the monograph gives 9.5 km2 (100% polygon) and 4.1 km2 (90% polygon), so the estimator alone changes the value by about 2.3 times | a summary; it cannot be the only source |
| 2 | `palomares2001a`, `palomares2001b`, `lopezbao2014` | READ IN FULL (2026-10-25):  a Word file of 2001a (no figures); 2001b in the browser; the accepted manuscript of `lopezbao2014` (its supporting figures S1 to S3 and Table S1 are not in the file) | `female_home_range_km2` and the overlap index | the range-size result of 2001a rests on five ranges (one inferred) and two predictors with r = -0.98, so the disagreement with the monograph is weak | `digital.csic.es/handle/10261/51457`, `.../51227`, `.../99118` |
| 3 | `ferreras1992` | READ IN FULL (2026-10-25; Word file) | annual mortality (the calibration parameter), shares of deaths from trapping and traffic | 30 radio-tagged lynx, 1983 to 1989, a declining Donana population:  0.37 with a 95% interval of 0.18 to 0.51; residents 0.12 and 0.21, dispersers 0.70 and 0.86; the trapping and road figures are shares of the rate, not of deaths | `digital.csic.es/handle/10261/50936` |
| 4 | `ferreras2004` | READ IN FULL (2026-10-25) | dispersal age, share of dispersers that settle | mean age at the start of dispersal 17.8 +/- 1.2 months; at least 13 of 27 dispersers (48%) settled and 7 fates were unknown | `digital.csic.es/handle/10261/50304` |
| 5 | `official_census_2010`, `official_census_2011`, `iberlince_censo2016` | READ (2026-10-25), in the issuer's own reports on `www.iberlince.eu` (11, 8, and 9 pages) | the history counts | they give 202, not 214, for Andujar-Cardena in 2011, see below | `www.iberlince.eu/files/images/docs/3_informeslife/` |
| 6 | `iberlince2017_census` | NOT READ; named only (the document was not located) | none directly | it lets sources that repeat the 2017 census count as one origin | not located |
| 7 | `mite_census2023`, `mite_census2024` | WEB PAGES ONLY (the census reports were not read) | none directly | context for later years, not for the 2002 to 2011 history test | MITECO press pages |

## Still unread, and not found in any source read

- The origin of the conversion "114 pellets per m2 is about 4.6 rabbits per hectare" (`palomares2001a`):  it is in none of the papers read, including the paper that `palomares2001a` cites for it.  Treat 4.6 as our assumption.

## The 2011 count has two values

`data/history/counts.csv` holds 214 lynx for Andujar-Cardena in 2011 (`catsg`, "including 90 adults").  The issuer's own documents give 202:  the 2016 report (original at `www.iberlince.eu`, 9 pages, read 2026-10-25; a copy on the Cortes de Aragon site agrees) and the 2011 report (8 pages).  The series gives total 53 in 2002, 190 in 2010, and **202 in 2011**; territorial females 43 in 2010 and 51 in 2011; occupied area 264 km2 in 2010 and 282 km2 in 2011.  The report's own sums agree (Sierra Morena 2011:  202 + 18 + 4 = 224; Andalusia 224 + 86 = 310).  We found no primary document that gives 214, and the reason for the difference is unknown.  The held-out target is Valerie's and Anastasiya's decision (recommendation:  202, bounds 181.8 to 222.2).

## Not done

- The counts of 2003 to 2009 in the official series were copied from the report and have not been audited against a second reading; the primary-source audit (`scripts/audit_sample.py`, #58) is the planned check.
- Several registry rows still say "abstract only" or "web page"; re-check a row when you read its source.
