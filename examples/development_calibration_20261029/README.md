# Development calibration, 2026-10-29

This is an exploratory calibration using 2002–2010 only, seed 20261029, 750 km² total area and 4.6 rabbits/hectare. It is not the preregistered final run. No 2011 simulation was run and no model default changed.

The earlier five uncalibrated trials at 37% annual mortality produced a median 2010 count of 36, versus the recorded 190. Calibration then used the existing `simulation.history.calibrate` function: 41 mortality settings (0.10–0.50, step 0.01), 100 trials per setting, 96 months. The closest median annual growth was 1.1687318733895244 at 17% mortality, inside 1.12–1.22. This fits an endpoint growth measure, not every yearly count or independent historical validation.

`calibration.json` records the entire grid and model/history code hashes; `input.json` records configuration and research hashes. Compare hashes before treating this saved record as applicable to changed code or inputs. Final freeze, calibration and held-out testing remain separate.

To reproduce, load this input and the research files with matching hashes using `load_parameters`, then call `history.calibrate(parameters, config, 20261029)`. Do not call `heldout` or `run_protocol` for this development-only check.
