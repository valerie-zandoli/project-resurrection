# Little lynx viewer

Turn one saved synthetic results file into an offline HTML viewer:

```sh
python -m report.lynx_viewer examples/live_claude_20261026/round_0/results.json --output /tmp/lynx-viewer.html
```

Open the resulting file in a browser. No server, internet connection, model call,
or API key is needed. The file contains the saved run and can be shared as an
ordinary HTML file. Choose a new output filename each time; existing files are
never overwritten. The same command accepts other schema-valid synthetic runs.

Play, pause, restart, choose a speed, step a month, or drag the month slider.
The counters and population curve use the recorded monthly history. The curve
shows the entire run; the orange marker follows the selected month. Births,
deaths, and patch crossings are monthly events, not cumulative totals.

The landscape and walking lynx are illustrations. The model currently saves
monthly population totals and final animal states, not monthly individual
positions. Symbols do not identify individual animals, and their placement
does not show actual patch occupancy, dispersal, territory, or geographic tracks.
Female/male colours represent aggregate counts. Up to 72 symbols are displayed;
larger populations show an explicit sampling label and exact counts above.
Areas and constant rabbit density are copied from the run configuration.

The exporter checks the results schema, run identity, complete monthly history,
population accounting, and final animal counts before displaying a file. It
does not replace the Evaluator's full checks, verify research provenance against
current source files, or establish historical/biological validation. Sample
fixtures remain explicitly labelled as samples. No simulation, handoff schema,
agent prompt, or biological rule changes are needed for this viewer.

Keyboard controls work through the native buttons and slider. Reduced-motion
settings disable decorative walking; playback starts only when requested.
