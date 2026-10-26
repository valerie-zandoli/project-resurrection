"""Run one explicitly provisional synthetic preview, never an agent workflow."""

import argparse
import csv
import json
from pathlib import Path

import jsonschema

from simulation.model import SETTLEMENT_RULES, normalize_config, preview_config, simulate, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', required=True,
                        help='acknowledge the still-proposed model conventions')
    parser.add_argument('--input', type=Path, help='version 2 input with actual research hashes')
    parser.add_argument('--seed', type=int, default=42, help='used when generating a default input')
    parser.add_argument('--months', type=int, default=12)
    parser.add_argument('--food', type=float, default=4.6, help='rabbits per hectare')
    parser.add_argument('--area', type=float, default=50, help='usable square kilometres per patch')
    parser.add_argument('--settlement-rule', choices=SETTLEMENT_RULES,
                        help='provisional female settlement rule; defaults to monthly current patch then other patch')
    parser.add_argument('--output', type=Path, required=True, help='new output directory; never overwritten')
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError('Output directory already exists; use a new directory')
        if args.input:
            config = json.loads(args.input.read_text())
        else:
            config = preview_config(args.seed, args.months, args.food, args.area)
        if args.settlement_rule is not None:
            config['settlement_rule'] = args.settlement_rule
            config['schema_version'] = '2.1'
        config = normalize_config(config)
        result = simulate(config)
        report = summary(result)
        args.output.mkdir(parents=True, exist_ok=False)
        for name, data in [('input', config), ('results', result), ('summary', report)]:
            (args.output / f'{name}.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
        with (args.output / 'history.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(result['history'][0]))
            writer.writeheader()
            writer.writerows(result['history'])
    except (OSError, ValueError, jsonschema.ValidationError) as exc:
        print(f'Preview failed: {exc}')
        return 1
    print(f'Preview saved to {args.output}. Historical validation: not assessed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
