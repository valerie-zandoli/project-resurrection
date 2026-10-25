"""Tables and a figure for the final report, drawn from a batch file written by `simulation.experiments`.

The figure is plain SVG written by this file, so no plotting library is needed.  A cell that did not
complete is shown as incomplete and never as a number.
"""

import argparse
import json
from pathlib import Path

PALETTE = ["#1f6feb", "#c2397a", "#2e9e5b", "#b45f06"]


def load_batch(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cells(batch):
    """Cells sorted by food level and then area; `stats` is None for a cell that is not complete."""
    if not batch["cells"]:
        raise ValueError("the batch has no cells")
    rows = []
    for cell in batch["cells"]:
        stats = cell.get("statistics") if cell.get("status") == "completed" else None
        rows.append(dict(name=cell["name"], food=cell["food_rabbits_per_ha"], area=cell["area_km2_per_patch"],
                         status=cell["status"], stats=stats))
    return sorted(rows, key=lambda row: (row["food"], row["area"]))


def pct(value):
    return f"{value:.2f}"


def markdown_table(batch):
    lines = ["| Food (per ha) | Area per patch (km2) | Trials | Persisted (95% interval) | Final population, median (10th to 90th) | Extinct | Median extinction month |",
             "|---|---|---|---|---|---|---|"]
    for row in cells(batch):
        s = row["stats"]
        if s is None:
            lines.append(f"| {row['food']} | {row['area']} | - | incomplete ({row['status']}) | - | - | - |")
            continue
        month = "none" if s["extinction_month_median"] is None else f"{s['extinction_month_median']:g}"
        lines.append(f"| {row['food']} | {row['area']} | {s['trials']} | "
                     f"{pct(s['persistence_share'])} ({pct(s['persistence_wilson_95'][0])} to {pct(s['persistence_wilson_95'][1])}) | "
                     f"{s['final_population_median']:g} ({s['final_population_p10']:g} to {s['final_population_p90']:g}) | "
                     f"{pct(s['extinction_share'])} | {month} |")
    return "\n".join(lines) + "\n"


def persistence_svg(batch, title="Share of trials that persisted, with 95% intervals"):
    rows = cells(batch)
    foods = sorted({row["food"] for row in rows})
    areas = sorted({row["area"] for row in rows})
    width, height, left, top, bottom = 760, 440, 70, 60, 90
    plot_h = height - top - bottom
    group_w = (width - left - 30) / len(foods)

    def y(value):
        return top + plot_h * (1 - value)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           'font-family="Helvetica, Arial, sans-serif">',
           f'<title>{title}</title><rect width="{width}" height="{height}" fill="#ffffff"/>',
           f'<text x="{width / 2}" y="28" text-anchor="middle" font-size="16" font-weight="700">{title}</text>']
    for tick in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<line x1="{left}" x2="{width - 30}" y1="{y(tick):.1f}" y2="{y(tick):.1f}" stroke="#dddddd"/>')
        out.append(f'<text x="{left - 8}" y="{y(tick) + 4:.1f}" text-anchor="end" font-size="12">{tick:g}</text>')
    for g, food in enumerate(foods):
        center = left + group_w * (g + 0.5)
        out.append(f'<text x="{center:.1f}" y="{height - bottom + 28}" text-anchor="middle" font-size="13">food {food:g} per ha</text>')
        for a, area in enumerate(areas):
            x = center + (a - (len(areas) - 1) / 2) * 56
            color = PALETTE[a % len(PALETTE)]
            row = next((r for r in rows if r["food"] == food and r["area"] == area), None)
            if row is None:
                continue
            s = row["stats"]
            if s is None:
                # No marker on the axis, so an incomplete cell cannot be read as 0%:  a dashed line and a label only.
                out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(1):.1f}" y2="{y(0):.1f}" stroke="#aaaaaa" stroke-width="1" stroke-dasharray="4 4"/>')
                out.append(f'<text x="{x:.1f}" y="{y(0.5):.1f}" text-anchor="middle" font-size="11" fill="#888888">incomplete</text>')
                continue
            low, high = s["persistence_wilson_95"]
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(low):.1f}" y2="{y(high):.1f}" stroke="{color}" stroke-width="3"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{y(s["persistence_share"]):.1f}" r="6" fill="{color}"/>')
    for a, area in enumerate(areas):
        out.append(f'<circle cx="{left + a * 150}" cy="{height - 24}" r="6" fill="{PALETTE[a % len(PALETTE)]}"/>')
        out.append(f'<text x="{left + a * 150 + 12}" y="{height - 20}" font-size="12">{area:g} km2 per patch</text>')
    out.append(f'<text x="{width - 30}" y="{height - 20}" text-anchor="end" font-size="11" fill="#777777">{batch.get("trials_per_cell", "?")} trials per cell; synthetic preview, not a history test</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path, help="batch.json from python -m simulation.experiments")
    parser.add_argument("--figure", type=Path, help="new SVG file; never overwritten")
    parser.add_argument("--table", type=Path, help="new Markdown file; never overwritten")
    args = parser.parse_args(argv)
    try:
        for target in (args.figure, args.table):
            if target is not None and target.exists():
                raise ValueError(f"{target} already exists; use a new name")
        batch = load_batch(args.batch)
        if args.figure:
            args.figure.write_text(persistence_svg(batch), encoding="utf-8")
        if args.table:
            args.table.write_text(markdown_table(batch), encoding="utf-8")
        if not (args.figure or args.table):
            print(markdown_table(batch), end="")
    except (OSError, ValueError, KeyError) as exc:
        print(f"Report figures failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
