"""Print the freeze-time values that docs/history-preregistration.md asks for.

Run it from the repository root at the freeze, with the code that will run checked out:

    python scripts/freeze_values.py --runner "Valerie Zandoli"

It reads the commit, the content hashes of the two research files, and the Python version, and prints the four
lines of the pre-registration section "TO FILL at the freeze", ready to paste.  It changes nothing, calls no model,
needs no key, and never runs the history test.

The hashes come from `validators.handoff_hashes.file_sha256`, the function that the harness uses, so a line ending
of CRLF reads as LF and every checkout gives the same value.

Exit code:  0 = the values were printed;  1 = the working tree has uncommitted changes (the commit would not
describe the code that runs; use --allow-dirty to print anyway);  2 = this is not a git checkout, or a research
file cannot be read.
"""

import argparse
import datetime
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validators.handoff_hashes import file_sha256  # noqa: E402

PARAMETERS = "data/parameters/iberian_lynx_baseline.csv"
SOURCES = "data/parameters/sources.csv"
EXPECTED_PYTHON = (3, 12)


class FreezeError(Exception):
    """A value could not be read."""


def git(root, *args, run=subprocess.run):
    done = run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise FreezeError(f"git {' '.join(args)} failed:  {done.stderr.strip() or 'no message'}")
    return done.stdout.strip()


def collect(root, *, run=subprocess.run, python_version=None, now=None):
    """Read the values from the checkout at `root`; raise FreezeError when one cannot be read."""
    root = Path(root)
    commit = git(root, "rev-parse", "HEAD", run=run)
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD", run=run)
    dirty = bool(git(root, "status", "--porcelain", run=run))
    try:
        tip = git(root, "rev-parse", "origin/develop", run=run)
    except FreezeError:
        tip = None
    hashes = {}
    for label, relative in (("parameters_csv", PARAMETERS), ("sources_csv", SOURCES)):
        try:
            hashes[label] = file_sha256(root / relative)
        except OSError as exc:
            raise FreezeError(f"{relative}:  cannot read the file ({exc.strerror or exc})") from exc
    stamp = now or datetime.datetime.now().astimezone()
    return dict(commit=commit, branch=branch, dirty=dirty,
                at_develop_tip=None if tip is None else tip == commit,
                hashes=hashes, python=python_version or platform.python_version(),
                read_at=stamp.isoformat(timespec="minutes"), date=stamp.date().isoformat())


def warnings(values):
    found = []
    if values["dirty"]:
        found.append("The working tree has uncommitted changes, so the commit does not describe the code that runs.")
    if values["at_develop_tip"] is False:
        found.append("HEAD is not the tip of origin/develop (as last fetched); check that this is the code to freeze.")
    major_minor = tuple(int(part) for part in values["python"].split(".")[:2])
    if major_minor != EXPECTED_PYTHON:
        found.append(f"Python {values['python']} is not {'.'.join(map(str, EXPECTED_PYTHON))}, the version the project uses.")
    return found


def format_lines(values, runner=None):
    """The four lines of "TO FILL at the freeze", then what was read and any warnings."""
    tip = {True: "yes", False: "no", None: "unknown (no origin/develop here)"}[values["at_develop_tip"]]
    lines = [
        f"- The commit of the code that will run (hash):  {values['commit']}",
        f"- The hashes of the two research files:  `{PARAMETERS}` {values['hashes']['parameters_csv']};  "
        f"`{SOURCES}` {values['hashes']['sources_csv']}",
        f"- The Python version:  {values['python']}",
        f"- The date and the name of the person who ran it:  {values['date']}, {runner or 'TO FILL (name)'}",
        "",
        f"Read at {values['read_at']} on branch {values['branch']}; HEAD is the tip of origin/develop:  {tip}.",
    ]
    lines += [f"WARNING:  {text}" for text in warnings(values)]
    return lines


def main(argv=None, *, run=subprocess.run):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="the checkout to read (default: this repository)")
    parser.add_argument("--runner", help="the name of the person who will run the history test")
    parser.add_argument("--allow-dirty", action="store_true", help="print the values although the tree is not clean")
    args = parser.parse_args(argv)
    try:
        values = collect(args.root, run=run)
    except FreezeError as exc:
        print(f"Cannot read the freeze values:  {exc}", file=sys.stderr)
        return 2
    if values["dirty"] and not args.allow_dirty:
        print("The working tree has uncommitted changes, so the commit would not describe the code that runs.  "
              "Commit or stash them, or use --allow-dirty.", file=sys.stderr)
        return 1
    print("\n".join(format_lines(values, args.runner)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
