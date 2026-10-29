# Local experiment controls

The title header shows a decorative rabbit hopping from Project to Resurrection
with a lynx following it. Pause/Play animation controls the header only. Reduced
motion keeps the animals still, and hiding the page pauses their animation.

Start from the repository root using the project's Python environment:

```sh
python -m report.experiment_controls --output /tmp/lynx-experiments --port 8767
```

Open the printed local address. Choose rabbit food density, land per patch,
starting population, duration and random seed, then select **Run my experiment**.
The food dropdown offers 1, 5, 15, 25, 35, 45 and 55 rabbits per hectare, with 5
selected initially. These are interface choices; the research breeding threshold
and the preregistered batch food levels remain unchanged.
The page runs the existing numerical simulator and embeds its saved viewer.
The simulation itself makes no AI calls. Changing a field does not change the displayed saved run
until a new run succeeds. Previous experiments can be selected during the session.

Each experiment gets a unique folder containing input.json, results.json,
summary.json, preview.json, viewer.html and a snapshot of its research files.
The preview record preserves research hashes and pilot evidence warnings.
Files remain on disk after the server stops; the page's experiment list lasts
only for the current page session. The saved viewer also opens offline.

Controls are bounded: 0–100 rabbits per hectare, 1–1,000 square kilometres per
patch, 4–200 starting lynxes in multiples of four, 1–120 months and a whole-number
seed from 0 to 4,294,967,295. Existing territory constraints still apply. Failed
experiments remove only their newly allocated incomplete folder. No previous
experiment is overwritten. A server session permits at most 100 saved runs.

These are synthetic pilot previews, not final experiment batches or historical
validation. Food remains constant and affects breeding under the existing model.
Rabbit symbols illustrate food density; individual rabbits and hunts are not
simulated. Animal positions and movement are illustrative.

The server binds only to 127.0.0.1, checks the request host, origin and session
token, limits request sizes, and runs one experiment at a time. It serves only
the named artifacts of runs completed during its lifetime, not arbitrary files.

## Send a saved experiment to the Evaluator

After a run finishes, select **Send to Evaluator**. This calls the existing Claude
Evaluator role through the bounded harness, using a fresh conversation. It must
call `check_artifacts`; the tool's verdict is the record, and Claude supplies a
separate explanation. The page shows pass, requested revisions, or stop, plus
every check and requested fix. A failed call is shown as incomplete, never pass.

Configure the ignored local `.env` with the project's existing provider settings.
If the key file lives in another checkout, pass its path without copying it:

```sh
python -m report.experiment_controls --output /tmp/lynx-experiments --env-file /path/to/project/.env
```

Only pressing the evaluation button makes paid Claude calls. The existing role
limits apply: at most four steps, with a 30-second timeout per provider request
and no automatic provider retries. There are at most three manually triggered
failed evaluation attempts per saved run in a server session. A completed review
is reused; clicking again does not pay for another review.

The Evaluator checks the saved input and results against their research snapshot.
It does not rerun the simulation or alter research, inputs or results. Snapshot
hashes are checked before sending; saved artifact hashes are checked again after
review. Each attempt gets a separate `reviews/review-.../` folder with a trace.
A completed attempt also saves `report.json` with the evaluation, explanation,
input hashes and model name. No credential is copied into these files. Earlier
failed attempts remain as diagnostics. The report can be downloaded from the page.

This connection uses the current artifact-checking Evaluator; it does not add a
full code audit, statistical review, historical validation or an automatic
Developer revision loop. A requested revision is shown for the owner to address.

## Research vs. this experiment

Every completed run displays a comparison panel from its own saved research
snapshot. It compares food with the breeding threshold and patch area with
female territory capacity. Simulated totals for the whole run are shown
separately from research estimates.

The table shows 13 inputs read by the current simulator: research baseline and
low–high range, value actually used (including overrides), source citation,
evidence note and confidence label. Litter size shows the model's low–high
sampling bounds rather than treating the published mean as a fixed number of
births. The source notes distinguish published evidence from team assumptions;
the ranges are not all statistical confidence intervals.

Food/season and territory rows show the associated Evaluator check after review.
Other rows say explicitly that no probability or scientific-validity verdict
was produced. No observed historical population is invented for synthetic
settings. Editing the form leaves the panel attached to the saved run until a
new run finishes or another saved run is chosen. The panel data is also saved
as `research-comparison.json` alongside the results.

## Preliminary historical comparison

To make one development-only comparison, using five trials of the current
uncalibrated model through 2010:

```sh
python -m report.history_preview --output /tmp/history-development-preview
python -m report.experiment_controls --output /tmp/lynx-experiments --history-preview /tmp/history-development-preview/report.json
```

The page shows observed 2002/2010 counts, simulated medians and min–max counts
across the five trials, differences and the growth comparison. This uses the
separate historical initialization (53 lynxes, including 25 adults), total area
750 square kilometres, food 4.6 and the research table's mortality, not the
interactive form's settings. Source keys identify the observed counts.

This is not calibration or the final history verdict. The seed is 20261028,
different from the preregistered final seed. The preview never calls calibration
or the held-out function and stops every trial at month 96 (2010). It never
computes a 2011 outcome. Five trials are a development check, not an accuracy
claim. The report, raw trial populations, input and research snapshot are saved
to a new folder; existing output is never overwritten. The history report is
read once at server startup and is independent of new interactive experiments.
Without --history-preview, the panel is hidden. This does not change the final
history procedure or its freeze requirements.
