"""The viewer must not silently invent or alter a saved population history."""
import copy
import json
import re
from pathlib import Path

import pytest

from report.lynx_viewer import export_viewer, render_viewer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def results():
    data = json.loads((ROOT / 'examples/handoffs/results.json').read_text())
    data['config']['duration_months'] = 2
    data['history'].append({**data['history'][-1], 'month': 2})
    return data


def embedded(html):
    return json.loads(re.search(r'<script type="application/json" id="run-data">(.*?)</script>',
                                html, re.S).group(1))


def test_recorded_history_is_preserved_without_claiming_individual_tracks(results):
    before = copy.deepcopy(results)
    html = render_viewer(results)
    data = embedded(html)
    assert data['history'] == results['history']
    assert data['config'] == results['config']
    assert data['data_kind'] == results['data_kind']
    assert 'final_animals' not in data
    assert results == before
    assert 'monthly animal tracks are not saved' in html


@pytest.mark.parametrize('mutation', ['accounting', 'month_gap', 'final_count'])
def test_inconsistent_run_is_rejected_before_export(results, mutation):
    if mutation == 'accounting':
        results['history'][1]['births'] += 1
    elif mutation == 'month_gap':
        del results['history'][1]
    else:
        animal = next(a for a in results['final_animals'] if a['sex'] == 'male')
        animal['alive'] = not animal['alive']
    with pytest.raises(ValueError):
        render_viewer(results)


def test_run_label_cannot_break_out_of_embedded_json(results):
    label = '</script><script>alert("untrusted")</script>&'
    results['run_id'] = results['config']['run_id'] = label
    html = render_viewer(results)
    assert label not in html
    assert embedded(html)['run_id'] == label


def test_report_does_not_overwrite_existing_output_or_source(results, tmp_path):
    source = tmp_path / 'results.json'
    source.write_text(json.dumps(results))
    output = tmp_path / 'viewer.html'
    export_viewer(source, output)
    saved = output.read_bytes()
    with pytest.raises(FileExistsError):
        export_viewer(source, output)
    assert output.read_bytes() == saved
    with pytest.raises(FileExistsError):
        export_viewer(source, source)
    assert json.loads(source.read_text()) == results


def test_non_finite_json_is_refused_without_partial_report(results, tmp_path):
    source, output = tmp_path / 'bad.json', tmp_path / 'viewer.html'
    results['config']['food_rabbits_per_ha'] = float('nan')
    source.write_text(json.dumps(results))
    with pytest.raises(ValueError, match='Non-finite'):
        export_viewer(source, output)
    assert not output.exists()
