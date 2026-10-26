"""Draw the 10 parameter rows that a person checks against the primary source before a batch.

The draw is reproducible:  the seed is the first 8 bytes of the SHA-256 of the batch run ID, so
another person gets the same rows (docs/handoff-decisions.md, "Primary-source audit").  The script
reads two CSV files and writes one Markdown file; it makes no network call.
"""

import argparse
import csv
import hashlib
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = "data/parameters/iberian_lynx_baseline.csv"
SOURCES = "data/parameters/sources.csv"
ROWS = 10


def seed_for(run_id):
    return int.from_bytes(hashlib.sha256(run_id.encode()).digest()[:8], "big")


def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def draw(run_id, parameters, count=ROWS):
    """Return `count` distinct rows, drawn from the rows sorted by name with the run ID's seed."""
    if not run_id.strip():
        raise ValueError("the batch run ID must not be empty")
    ordered = sorted(parameters, key=lambda row: row["name"])
    if not 1 <= count <= len(ordered):
        raise ValueError(f"cannot draw {count} rows from {len(ordered)}")
    return random.Random(seed_for(run_id)).sample(ordered, count)


def cell(text):
    return text.replace("|", "/").replace("\n", " ").strip()


def render(run_id, rows, sources):
    by_key = {row["key"]: row for row in sources}
    lines = [f"# Primary-source audit, batch {run_id}", "",
             f"Seed: the first 8 bytes of SHA-256 of the run ID, which is {seed_for(run_id)}.  "
             "Rows are drawn from the table sorted by name, so another person gets the same rows.", "",
             "For each row, open the primary source and check that the value or range appears in it and that "
             "the source supports the claim.  Write `correct`, `incorrect`, or `unavailable` (a source that "
             "cannot be reached is reported apart).  Bar:  9 of 10 correct, or the batch stops.", "",
             "| # | Parameter | Baseline (low to high) | Units | Group | Sources and how each was read | Result | Note |",
             "|---|---|---|---|---|---|---|---|"]
    for number, row in enumerate(rows, 1):
        keys = [key for key in row["source"].split(";") if key]
        read_as = "; ".join(f"{key} ({cell(by_key[key]['how_read']) if key in by_key else 'not in the registry'})"
                            for key in keys)
        lines.append(f"| {number} | `{row['name']}` | {row['baseline']} ({row['low']} to {row['high']}) | "
                     f"{cell(row['units'])} | {cell(row['area_age_group'])} | {read_as} |  |  |")
    lines += ["", "## Running table (one row per batch)", "",
              "| Batch | Rows checked | Correct | Unavailable | Running total correct |",
              "|---|---|---|---|---|",
              f"| {run_id} | {len(rows)} |  |  |  |", "",
              "Review the audit design if the running total falls below 90% after 30 rows (a guess)."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="the batch run ID; it is the only seed")
    parser.add_argument("--output", type=Path, required=True, help="new Markdown file; never overwritten")
    parser.add_argument("--rows", type=int, default=ROWS)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Output file already exists; use a new name")
        rows = draw(args.run_id, read(args.root / PARAMETERS), args.rows)
        args.output.write_text(render(args.run_id, rows, read(args.root / SOURCES)), encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        print(f"Audit draw failed: {exc}")
        return 1
    print(f"Audit sheet saved to {args.output}  (seed {seed_for(args.run_id)}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
