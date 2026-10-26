"""Run one case through the offline harness skeleton (no model, no key)."""

import argparse
from pathlib import Path

from harness.evidence_gate import STAGES
from harness.run_case import HarnessError, run_case


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", required=True,
                        help="acknowledge the still-proposed model conventions")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--food", type=float, default=4.6, help="rabbits per hectare")
    parser.add_argument("--area", type=float, default=50, help="usable square kilometres per patch")
    parser.add_argument("--stage", choices=STAGES, default="pilot",
                        help="a final run is refused when a contradiction check is not done")
    parser.add_argument("--output", type=Path, required=True, help="new case folder; never overwritten")
    args = parser.parse_args(argv)
    try:
        result = run_case(args.output, options=dict(seed=args.seed, months=args.months,
                                                    food=args.food, area=args.area, stage=args.stage))
    except HarnessError as exc:
        print(f"Harness failed to start: {exc}")
        return 2
    print(f"Case {result.status} after {result.attempts} attempt(s):  {result.reason}.  Saved to {result.run_dir}.")
    for warning in (result.evidence or {}).get("warnings", []):
        print(f"Evidence warning:  {warning}")
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
