# Compare the two breeding rules

This command depends on the gradual option in PR #96. It reads completed
synthetic batches without calling Claude or running the held-out history test.

First produce separate threshold and linear batches with the same seed, trial
count, duration, settlement rule, research files, and code version. The commands
are in `docs/linear-breeding-sensitivity.md`. Then run from the repository root:

```sh
python -m scripts.compare_breeding_runs --threshold /tmp/lynx-step-batch/batch.json --linear /tmp/lynx-linear-batch/batch.json --output /tmp/breeding-comparison.md
```

Use a new output filename. The report shows persistence and 95% Wilson intervals,
the difference in persistence in percentage points, median final population,
extinction share, and median extinction time among extinct trials. With no
extinctions it says “no extinctions observed.” Individual-share intervals are not
a test of the difference; no statistical significance or biological preference
is inferred.

Before comparing, the command checks complete batches, all trial artifacts,
the saved research hashes against the supplied research root, and the existing
Evaluator checks. It recomputes summaries and statistics from actual results
and rejects a mismatch with the saved summaries/statistics. It requires matching
trial seeds and identical inputs apart from run identity, breeding rule, and
the schema version needed for that rule. Code fingerprints, settlement rules,
and scenario cells must also match. It never silently drops a failed trial.

`--root` can name the research snapshot used for the saved batches; by default it
uses the repository. Changed research files fail the hash check. To compare old
saved batches, preserve their original research files rather than updating hashes.

The comparison preserves the status `historical_validation: not_assessed`.
Both breeding shapes are model assumptions, and this report does not establish
which one describes real lynx. Small test batches verify the reporting path;
they do not replace the agreed pilot or final experiments.
