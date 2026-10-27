"""A read-only snapshot of the two research files, made by the harness and never by an agent.

The Researcher is the only writer of these files.  The Developer and the Evaluator read the
snapshot, so a run is judged against the bytes that it was built from.
"""

import os
import shutil
from pathlib import Path

from validators.handoff_hashes import file_sha256

RESEARCH_FILES = ("data/parameters/iberian_lynx_baseline.csv", "data/parameters/sources.csv")


def make_snapshot(source_root, snapshot_root):
    """Copy the research files under the same relative paths, mode 444, and return their hashes."""
    snapshot_root = Path(snapshot_root)
    if snapshot_root.exists():
        raise FileExistsError(f"snapshot folder already exists: {snapshot_root}")
    hashes = {}
    for relative in RESEARCH_FILES:
        target = snapshot_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(source_root) / relative, target)
        os.chmod(target, 0o444)
        hashes[relative] = file_sha256(target)
    return hashes
