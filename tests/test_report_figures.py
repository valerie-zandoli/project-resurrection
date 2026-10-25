"""The report tables and figure:  numbers from the batch file, incomplete cells never shown as numbers."""

import json
import xml.dom.minidom

import pytest

from report import figures


def stats(share, low, high, median=13.0, p10=3.0, p90=31.0, extinct=0.05, month=101):
    return dict(trials=100, persistence_share=share, persistence_wilson_95=[low, high],
                final_population_median=median, final_population_p10=p10, final_population_p90=p90,
                extinction_share=extinct, extinction_month_median=month)


def batch(incomplete=False):
    grid = [(1, 50, 0.0, 3.5e-18, 0.037, 0.78, 82), (1, 100, 0.0, 0.0, 0.037, 0.8, 77.5),
            (4.6, 50, 0.58, 0.48, 0.67, 0.05, 101), (4.6, 100, 0.6, 0.5, 0.69, 0.03, 100),
            (55, 50, 0.68, 0.58, 0.76, 0.03, None), (55, 100, 0.49, 0.39, 0.59, 0.06, 110.5)]
    out = []
    for food, area, share, low, high, extinct, month in grid:
        out.append(dict(name=f"food-{food}_area-{area}", food_rabbits_per_ha=food, area_km2_per_patch=area,
                        planned_trials=100, status="completed",
                        statistics=stats(share, low, high, extinct=extinct, month=month)))
    if incomplete:
        out[-1].update(status="failed", statistics=None)
    return dict(trials_per_cell=100, cells=out)


def test_cells_are_sorted_by_food_then_area():
    shuffled = batch()
    shuffled["cells"].reverse()
    assert [(c["food"], c["area"]) for c in figures.cells(shuffled)] == [(1, 50), (1, 100), (4.6, 50), (4.6, 100), (55, 50), (55, 100)]


def test_the_table_shows_the_numbers_to_two_decimals_and_none_for_no_extinction():
    table = figures.markdown_table(batch())
    assert "| 4.6 | 50 | 100 | 0.58 (0.48 to 0.67) | 13 (3 to 31) | 0.05 | 101 |" in table
    assert "| 1 | 50 | 100 | 0.00 (0.00 to 0.04) |" in table
    assert "| 55 | 50 | 100 | 0.68 (0.58 to 0.76) | 13 (3 to 31) | 0.03 | none |" in table
    assert table.count("\n| ") == 6


def test_an_incomplete_cell_is_never_shown_as_a_number():
    table = figures.markdown_table(batch(incomplete=True))
    assert "incomplete (failed)" in table
    svg = figures.persistence_svg(batch(incomplete=True))
    assert "incomplete" in svg and svg.count("<circle") == 5 + 1 + 2  # five points, one hollow, two legend dots


def test_the_figure_is_valid_svg_with_one_point_and_one_interval_per_complete_cell():
    svg = figures.persistence_svg(batch())
    xml.dom.minidom.parseString(svg)
    assert svg.count('stroke-width="3"') == 6
    assert "food 4.6 per ha" in svg and "100 trials per cell" in svg and "not a history test" in svg


def test_the_command_writes_a_figure_and_a_table_and_never_overwrites(tmp_path, capsys):
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(batch()))
    args = [str(path), "--figure", str(tmp_path / "f.svg"), "--table", str(tmp_path / "t.md")]
    assert figures.main(args) == 0
    xml.dom.minidom.parse(str(tmp_path / "f.svg"))
    assert "Persisted (95% interval)" in (tmp_path / "t.md").read_text()
    assert figures.main(args) == 1 and "already exists" in capsys.readouterr().out
    assert figures.main([str(tmp_path / "missing.json")]) == 1


def test_with_no_output_option_the_table_is_printed(tmp_path, capsys):
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(batch()))
    assert figures.main([str(path)]) == 0
    assert "| Food (per ha)" in capsys.readouterr().out
