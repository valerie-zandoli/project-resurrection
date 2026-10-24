"""Check that every handoff in one run names the same research files.

A content hash is a short fingerprint of a file's contents.  It proves two
agents read the same bytes; it does not prove the file is correct.
"""

import hashlib
from pathlib import Path

FIELDS = (("parameters_csv", "parameters_sha256"), ("sources_csv", "sources_sha256"))


def file_sha256(path):
    """Hash a file with CRLF line endings read as LF, so every checkout agrees."""
    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def check_handoff_hashes(run_input, results, evaluation=None):
    """Return errors when the handoffs of one run disagree on the file hashes.

    Pure comparison of three parsed JSON documents; it reads no files.
    """
    errors = []
    for _, hash_field in FIELDS:
        expected = run_input[hash_field]
        if results["config"][hash_field] != expected:
            errors.append(f"results.config.{hash_field} differs from the input")
        if evaluation is not None and evaluation[hash_field] != expected:
            errors.append(f"evaluation.{hash_field} differs from the input")
    return errors


def check_files_current(run_input, root="."):
    """Return errors when a file on disk no longer matches the hash in the input.

    A deliberate change by the Researcher is not a revision of this run: the
    harness starts a new run from a fresh input with new hashes.
    """
    errors = []
    for path_field, hash_field in FIELDS:
        path = Path(root) / run_input[path_field]
        try:
            actual = file_sha256(path)
        except OSError as exc:
            errors.append(f"{run_input[path_field]}: cannot read file: {exc}")
            continue
        if actual != run_input[hash_field]:
            errors.append(f"{run_input[path_field]}: changed since the input recorded its hash")
    return errors
