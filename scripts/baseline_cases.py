"""Build the case files for planted flaws 7 and 8 of docs/baseline-test.md.

Flaw 7:  a conflict named in the research notes is dropped from the table (the `contradicts` cell says
`none_identified`).  Flaw 8:  a source that only repeats another study is added as if it were independent
(its `origin` is relabeled and the confidence is raised).

Both cases still pass `validators.parameters`:  the validator checks structure, not meaning, so only an
arm that reads the sources can catch them.  The output holds three folders named case-1 to case-3 in a
random order, so a name never says which case is which; the truth (which folder is valid, flaw7, or flaw8)
is written to a key file beside the output folder, never inside it.  Keep the key from the arms until scoring.
"""

import argparse
import csv
import json
import random
import secrets
import sys
from pathlib import Path

SENTINELS = {"none_identified", "not_checked"}
CASES = ("valid", "flaw7", "flaw8")


def blinded_names(seed):
    """Map each case to a folder name that does not reveal it:  case-1 to case-3 in a seeded random order."""
    names = [f"case-{number}" for number in range(1, len(CASES) + 1)]
    random.Random(seed).shuffle(names)
    return dict(zip(CASES, names))


def read_table(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        return list(reader.fieldnames), [dict(row) for row in reader]


def write_table(path, fields, rows):
    """Every case file is written here, in one format (UTF-8, no BOM, LF), so no folder stands out."""
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def split(value):
    return [part.strip() for part in value.split(";") if part.strip()]


def find(rows, column, value, what):
    for row in rows:
        if row[column] == value:
            return row
    raise ValueError(f"{what} {value!r} not found")


def drop_contradiction(evidence_rows, row_name):
    """Flaw 7: replace the named contradictions of one row with `none_identified`; return the truth."""
    row = find(evidence_rows, "name", row_name, "evidence row")
    dropped = split(row["contradicts"])
    if not dropped or dropped[0] in SENTINELS:
        raise ValueError(f"{row_name!r} names no contradiction to drop")
    cleared_note = row["draft_note"]
    row["contradicts"] = "none_identified"
    row["draft_note"] = ""
    return {"flaw": 7, "parameter": row_name, "dropped_contradictions": dropped,
            "draft_note_cleared": cleared_note,
            "truth": "the table says no source disagrees, but the sources named in the dropped entries do"}


def double_count_origin(parameter_rows, source_rows, evidence_rows, row_name, extra_source, new_origin):
    """Flaw 8: add a source that repeats a study already in the row, under a new origin; return the truth."""
    parameter = find(parameter_rows, "name", row_name, "parameter")
    evidence = find(evidence_rows, "name", row_name, "evidence row")
    source = find(source_rows, "key", extra_source, "source")
    if extra_source in split(parameter["source"]):
        raise ValueError(f"{extra_source!r} is already cited by {row_name!r}")
    row_origins = split(evidence["origin"])
    repeated = sorted(set(split(source["origin"])) & set(row_origins))
    if not repeated:
        raise ValueError(f"{extra_source!r} repeats none of the origins of {row_name!r}: {row_origins}")
    used = {origin for each in source_rows for origin in split(each["origin"])}
    if new_origin in used:
        raise ValueError(f"origin {new_origin!r} is already in use; pick a new one")
    before = {"source": parameter["source"], "origin": evidence["origin"], "confidence": evidence["confidence"],
              "confidence_reason": evidence["confidence_reason"], "source_origin": source["origin"]}
    parameter["source"] = f"{parameter['source']};{extra_source}"
    source["origin"] = new_origin
    evidence["origin"] = f"{evidence['origin']};{new_origin}"
    evidence["confidence"] = "high"
    evidence["confidence_reason"] = "Independent sources agree."
    return {"flaw": 8, "parameter": row_name, "added_source": extra_source, "really_repeats": repeated,
            "before": before, "truth": f"{extra_source} repeats {', '.join(repeated)}; the table counts it as a separate origin"}


def build(parameters, sources, evidence, output, row7, row8, extra_source, new_origin, key_path=None, blind_seed=None):
    output = Path(output)
    key_path = Path(key_path) if key_path else output.with_name(output.name + "-key.json")
    if output.exists():
        raise ValueError(f"{output} already exists; use a new folder")
    if key_path.exists():
        raise ValueError(f"{key_path} already exists; use a new file")
    if output.resolve() in key_path.resolve().parents:
        raise ValueError("the key must not be inside the case folder; the arms would see it")
    blind_seed = secrets.randbits(32) if blind_seed is None else blind_seed
    folders = blinded_names(blind_seed)
    files = {"parameters": Path(parameters), "sources": Path(sources), "evidence": Path(evidence)}
    tables = {name: read_table(path) for name, path in files.items()}
    names = {"parameters": "parameters.csv", "sources": "sources.csv", "evidence": "evidence.csv"}

    flaw7 = {name: (fields, [dict(row) for row in rows]) for name, (fields, rows) in tables.items()}
    key7 = drop_contradiction(flaw7["evidence"][1], row7)
    flaw8 = {name: (fields, [dict(row) for row in rows]) for name, (fields, rows) in tables.items()}
    key8 = double_count_origin(flaw8["parameters"][1], flaw8["sources"][1], flaw8["evidence"][1],
                               row8, extra_source, new_origin)

    output.mkdir(parents=True)
    # Write every file of every case, even an unchanged one:  a byte copy would keep the input's line endings
    # and BOM, and the folder with the original bytes would give itself away.
    for case, case_tables in (("valid", tables), ("flaw7", flaw7), ("flaw8", flaw8)):
        folder = folders[case]
        (output / folder).mkdir()
        for name in files:
            write_table(output / folder / names[name], *case_tables[name])
    key_path.write_text(json.dumps({"folders": folders, "blind_seed": blind_seed, "flaw7": key7, "flaw8": key8},
                                   indent=2) + "\n", encoding="utf-8")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new folder; never overwritten")
    parser.add_argument("--key", type=Path, help="new key file, outside the output folder (default: <output>-key.json)")
    parser.add_argument("--blind-seed", type=int, help="seed of the folder order (default: random; the key records it)")
    parser.add_argument("--row7", default="breeding_age_min", help="row whose named conflict is dropped")
    parser.add_argument("--row8", default="rabbit_density_spring_min_for_territorial_breeding",
                        help="row that gets the repeated source")
    parser.add_argument("--extra-source", default="eu_spain_report2018", help="source that repeats a study in row8")
    parser.add_argument("--new-origin", default="eu_spain_report2018_as_own_study",
                        help="the false origin label for the repeated source")
    args = parser.parse_args(argv)
    try:
        out = build(args.parameters, args.sources, args.evidence, args.output,
                    args.row7, args.row8, args.extra_source, args.new_origin, args.key, args.blind_seed)
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        print(f"Baseline cases failed: {exc}")
        return 1
    key_file = args.key or out.with_name(out.name + "-key.json")
    print(f"Cases written to {out} (case-1 to case-3, blinded); the key is {key_file}:  keep it from the arms.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
