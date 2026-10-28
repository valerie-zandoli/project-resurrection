# Local experiment controls

Start from the repository root using the project's Python environment:

```sh
python -m report.experiment_controls --output /tmp/lynx-experiments --port 8767
```

Open the printed local address. Choose rabbit food density, land per patch,
starting population, duration and random seed, then select **Run my experiment**.
The page runs the existing numerical simulator and embeds its saved viewer.
It makes no AI calls. Changing a field does not change the displayed saved run
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
