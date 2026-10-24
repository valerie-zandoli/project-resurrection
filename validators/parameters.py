"""Validate the research CSV handoff without judging its biological accuracy."""

import argparse
import csv
import math
from pathlib import Path

COLUMNS = (
    "name", "baseline", "low", "high", "units", "area_age_group",
    "source", "evidence_or_assumption",
)


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


def validate_parameters(parameters, sources):
    """Return all format/reference errors. Empty list means the handoff is valid."""
    errors = []
    source_rows = _read(sources, ("key",), errors)
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
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parameters", type=Path)
    parser.add_argument("sources", type=Path)
    args = parser.parse_args()
    errors = validate_parameters(args.parameters, args.sources)
    if errors:
        print("Validation failed:\n" + "\n".join(errors))
        return 1
    print("Parameter table passed format and source-reference checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
