# Parameter handoff validator

Owner: Anastasiya. Run from the repository root with Python 3.12:

```bash
python -m validators.parameters data/parameters/iberian_lynx_baseline.csv data/parameters/sources.csv
python -m pytest
```

The research CSV requires exactly these eight named columns (order may vary):
`name,baseline,low,high,units,area_age_group,source,evidence_or_assumption`.
Numbers must be finite, with `low <= baseline <= high`. Names must be unique.
Every field must be nonempty. Semicolon-separated source keys must each exist in
the source registry's `key` column; registry keys must be nonempty and unique.
Standard quoted CSV text, decimals, and a UTF-8 BOM are supported.
Failures report file, line, and parameter when available; the command exits 1.
Success exits 0. No AI credentials or third-party runtime dependencies are needed.

These are structural checks, not proof that a source supports a claim. Evaluators
must review biological plausibility, units, evidence quality, and assumptions.
Do not impose 0–1 limits on every parameter: counts, areas, and sex ratios have
other meanings. Parameter-specific biological checks belong in a later layer.

## Accepted research design

- Keep fixed female home range in the baseline. Compute whole female territory
  slots by rounding patch area / female home range down. A food-dependent range
  is a separate sensitivity scenario, not an established biological relationship.
- Use three food levels by two habitat conditions; define the actual settings
  before experiments. Similar medium/high outcomes can be valid.
- The proposed Andujar-Cardena historical comparison uses transferred Donana
  parameters. Document that limitation and the single held-out 2011 count.
  Agree on tolerance before runs and separate calibration from validation.
- Keep historical initialization separate from the synthetic 20-lynx experiment
  (10 females and 10 males). This validator does not implement the model.

The data files remain owned by Valerie and may arrive through a separate PR.
