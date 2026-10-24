"""Validate the research CSV handoff without judging its biological accuracy."""

import argparse
import csv
import math
from pathlib import Path

COLUMNS = (
    "name", "baseline", "low", "high", "units", "area_age_group",
    "source", "evidence_or_assumption",
)
EVIDENCE_COLUMNS = (
    "name", "confidence", "confidence_reason", "contradicts", "origin", "draft_note",
)
CONFIDENCE_LABELS = {"low", "medium", "high"}


def _split_list(value):
    """Split a semicolon-separated field and report empty or repeated entries."""
    values = [part.strip() for part in value.split(";")]
    if not value.strip() or any(not part for part in values):
        return None
    if len(values) != len(set(values)):
        return None
    return values


def _read(path, required, errors, exact=False):
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            fields = reader.fieldnames or []
            if len(fields) != len(set(fields)):
                errors.append(f"{path}: duplicate column names")
            if not set(required).issubset(fields) or (exact and set(fields) != set(required)):
                errors.append(f"{path}: expected columns: {', '.join(required)}")
                return []
            rows = []
            for row in reader:
                line = reader.line_num
                if None in row or any(value is None for value in row.values()):
                    errors.append(f"{path}:{line}: wrong number of CSV fields")
                    continue
                rows.append((line, {key: value.strip() for key, value in row.items()}))
            return rows
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"{path}: cannot read CSV: {exc}")
        return []


def _validate_evidence_rows(parameters, sources, evidence, errors):
    evidence_rows = _read(evidence, EVIDENCE_COLUMNS, errors, exact=True)
    if not evidence_rows:
        errors.append(f"{evidence}: no evidence records")

    parameters_by_name = {row["name"]: row for _, row in parameters}
    sources_by_key = {row["key"]: row for _, row in sources if row.get("key")}
    evidence_names = set()

    for line, row in evidence_rows:
        name = row["name"]
        prefix = f"{evidence}:{line} ({name or 'unnamed'})"
        if not name:
            errors.append(f"{prefix}: name is required")
        if name in evidence_names:
            errors.append(f"{prefix}: duplicate evidence parameter name")
        evidence_names.add(name)
        parameter = parameters_by_name.get(name)
        if parameter is None:
            errors.append(f"{prefix}: parameter name is not in the parameter table")

        if row["confidence"] not in CONFIDENCE_LABELS:
            errors.append(f"{prefix}: confidence must be low, medium, or high")
        if not row["confidence_reason"]:
            errors.append(f"{prefix}: confidence_reason is required")

        origins = _split_list(row["origin"])
        if origins is None:
            errors.append(f"{prefix}: origin must contain unique, nonempty semicolon-separated IDs")
        elif parameter is not None:
            cited_sources = _split_list(parameter["source"])
            allowed_origins = set()
            if cited_sources is not None:
                for key in cited_sources:
                    source = sources_by_key.get(key)
                    if source is not None:
                        source_origins = _split_list(source.get("origin", ""))
                        if source_origins is not None:
                            allowed_origins.update(source_origins)
            for origin in origins:
                if origin not in allowed_origins:
                    errors.append(f"{prefix}: origin {origin!r} is not listed by a cited source")

        contradictions = _split_list(row["contradicts"])
        if contradictions is None:
            errors.append(f"{prefix}: contradicts must contain unique, nonempty semicolon-separated entries")
            continue
        sentinels = {"none_identified", "not_checked"}
        if any(value in sentinels for value in contradictions) and len(contradictions) != 1:
            errors.append(f"{prefix}: none_identified and not_checked must stand alone")
            continue
        if contradictions[0] in sentinels:
            continue
        for contradiction in contradictions:
            if contradiction.startswith("source:"):
                pair = contradiction.split("~")
                if (len(pair) != 2 or not pair[0].startswith("source:")
                        or not pair[1].startswith("source:")):
                    errors.append(f"{prefix}: invalid source contradiction {contradiction!r}")
                    continue
                left, right = pair[0][len("source:"):], pair[1][len("source:"):]
                if not left or not right or left == right:
                    errors.append(f"{prefix}: source contradiction must name two different sources")
                for key in (left, right):
                    if key not in sources_by_key:
                        errors.append(f"{prefix}: unknown source in contradiction: {key!r}")
            elif contradiction.startswith("parameter:"):
                other = contradiction[len("parameter:"):]
                if not other or other == name or other not in parameters_by_name:
                    errors.append(f"{prefix}: unknown or invalid parameter contradiction: {other!r}")
            else:
                errors.append(f"{prefix}: invalid contradiction entry {contradiction!r}")

    for name in sorted(set(parameters_by_name) - evidence_names):
        errors.append(f"{evidence}: missing evidence row for parameter {name!r}")


def validate_parameters(parameters, sources, evidence=None):
    """Return all format/reference errors. Empty list means the handoff is valid."""
    errors = []
    source_rows = _read(sources, ("key", "origin") if evidence else ("key",), errors)
    keys = set()
    for line, row in source_rows:
        key = row["key"]
        if not key or key in keys:
            errors.append(f"{sources}:{line}: source key must be nonempty and unique: {key!r}")
        keys.add(key)
    if not source_rows:
        errors.append(f"{sources}: no source records")
    rows = _read(parameters, COLUMNS, errors, exact=True)
    names = set()
    if not rows:
        errors.append(f"{parameters}: no parameter records")
    for line, row in rows:
        prefix = f"{parameters}:{line} ({row['name'] or 'unnamed'})"
        for column in COLUMNS:
            if not row[column]:
                errors.append(f"{prefix}: {column} is required")
        if row["name"] in names:
            errors.append(f"{prefix}: duplicate parameter name")
        names.add(row["name"])
        numbers = {}
        for column in ("baseline", "low", "high"):
            try:
                number = float(row[column])
                if not math.isfinite(number):
                    raise ValueError
                numbers[column] = number
            except ValueError:
                errors.append(f"{prefix}: {column} must be a finite number")
        if len(numbers) == 3 and not numbers["low"] <= numbers["baseline"] <= numbers["high"]:
            errors.append(f"{prefix}: require low <= baseline <= high")
        for key in row["source"].split(";"):
            key = key.strip()
            if not key or key not in keys:
                errors.append(f"{prefix}: unknown or empty source key: {key!r}")
    if evidence:
        _validate_evidence_rows(rows, source_rows, evidence, errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parameters", type=Path)
    parser.add_argument("sources", type=Path)
    parser.add_argument(
        "--evidence", type=Path,
        help="optional evidence-column handoff to validate against the parameter and source tables",
    )
    args = parser.parse_args()
    errors = validate_parameters(args.parameters, args.sources, evidence=args.evidence)
    if errors:
        print("Validation failed:\n" + "\n".join(errors))
        return 1
    print("Parameter and evidence tables passed format and reference checks." if args.evidence
          else "Parameter table passed format and source-reference checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
