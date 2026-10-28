# Local experiment controls

Start from the repository root using the project's Python environment:

```sh
python -m report.experiment_controls --output /tmp/lynx-experiments --port 8767
```

Open the printed local address. Choose rabbit food density, land per patch,
starting population, duration and random seed, then select **Run my experiment**.
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
