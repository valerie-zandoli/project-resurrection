"""A read-only snapshot of the two research files, made by the harness and never by an agent.

The Researcher is the only writer of these files.  The Developer and the Evaluator read the
snapshot, so a run is judged against the bytes that it was built from.
"""

import os
import shutil
from pathlib import Path

from validators.evidence_gate import EVIDENCE_FILE
from validators.handoff_hashes import file_sha256

RESEARCH_FILES = ("data/parameters/iberian_lynx_baseline.csv", "data/parameters/sources.csv")
SNAPSHOT_FILES = (*RESEARCH_FILES, EVIDENCE_FILE)


def make_snapshot(source_root, snapshot_root):
    """Copy the research files under the same relative paths, mode 444, and return their hashes."""
    snapshot_root = Path(snapshot_root)
    if snapshot_root.exists():
        raise FileExistsError(f"snapshot folder already exists: {snapshot_root}")
    hashes = {}
    for relative in SNAPSHOT_FILES:
        source = Path(source_root) / relative
        # The evidence file is optional in a pilot; the evidence gate warns when it is absent.
        if relative == EVIDENCE_FILE and not source.is_file():
            continue
        target = snapshot_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        os.chmod(target, 0o444)
        hashes[relative] = file_sha256(target)
    return hashes


def check_snapshot_current(hashes, snapshot_root):
    """Return errors when any snapshotted research input changes during a case."""
    errors = []
    for relative, expected in hashes.items():
        path = Path(snapshot_root) / relative
        try:
            actual = file_sha256(path)
        except OSError as exc:
            errors.append(f"{relative}: cannot read snapshot: {exc}")
            continue
        if actual != expected:
            errors.append(f"{relative}: changed since the snapshot was made")
    return errors
