"""Export a saved synthetic run as a self-contained, offline animated viewer."""

import argparse
import json
from pathlib import Path

import jsonschema

from validators.results_checks import (
    check_accounting, check_animals, check_final_counts, check_identity, check_months,
)

ROOT = Path(__file__).resolve().parents[1]


def render_viewer(results):
    """Show recorded monthly totals; never infer individual monthly tracks."""
    schema = json.loads((ROOT / 'schemas/results.schema.json').read_text())
    jsonschema.validate(results, schema)
    config = results['config']
    for check in (check_identity, check_months, check_accounting, check_animals, check_final_counts):
        passed, detail, _ = check(config, results, {})
        if not passed:
            raise ValueError(detail)
    # Deliberately omit final animal states: they cannot reconstruct monthly tracks.
    payload = {key: results[key] for key in ('run_id', 'seed', 'data_kind', 'config', 'history')}
    encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False)
    for char, escaped in (('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e')):
        encoded = encoded.replace(char, escaped)
    template = (Path(__file__).with_name('lynx_viewer.html')).read_text(encoding='utf-8')
    return template.replace('__RUN_DATA__', encoded)


def export_viewer(source, output):
    source, output = Path(source), Path(output)
    with source.open(encoding='utf-8') as handle:
        results = json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f'Non-finite JSON number: {value}')))
    html = render_viewer(results)
    # Exclusive create preserves existing reports, including the input itself.
    with output.open('x', encoding='utf-8') as handle:
        handle.write(html)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        export_viewer(args.results, args.output)
    except (OSError, ValueError, jsonschema.ValidationError) as error:
        parser.exit(2, f'Could not export viewer: {type(error).__name__}. Check the results and output path.\n')
    print(f'Open {args.output.resolve()} in your browser. No server or API key needed.')


if __name__ == '__main__':
    main()
