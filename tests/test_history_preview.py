"""A development comparison must never consume the reserved 2011 batch."""
import json

import pytest

from report import history_preview as preview


def test_preview_stops_at_2010_without_calibration_or_heldout(tmp_path, monkeypatch):
    original = preview.history.run_trial_detail
    calls = []
    def guarded(p, config, seed, months, observe):
        assert months == 96 and config['duration_months'] == 96 and observe == ()
        calls.append(seed)
        return original(p, config, seed, months, observe)
    def forbidden(*args, **kwargs):
        pytest.fail('A development preview must not calibrate or run held-out trials')
    monkeypatch.setattr(preview.history, 'run_trial_detail', guarded)
    monkeypatch.setattr(preview.history, 'heldout', forbidden)
    monkeypatch.setattr(preview.history, 'calibrate', forbidden)
    folder = tmp_path / 'preview'
    report = preview.build_preview(folder)
    assert len(calls) == 5 and len(set(calls)) == 5
    assert report['seed'] != 20261101
    assert report['heldout_run'] is False and report['calibrated'] is False
    assert report['historical_validation'] == 'not_assessed'
    assert [row['observed'] for row in report['rows']] == [53, 190]
    populations = json.loads((folder / 'trial-populations.json').read_text())
    assert all(len(run) == 97 for run in populations)
    row = report['rows'][1]
    assert row['difference'] == row['simulated_median'] - 190
    assert row['difference_percent'] == 100 * row['difference'] / 190
    panel = preview.read_panel(folder / 'report.json')
    assert panel['rows'] == report['rows']
    assert 'research_sha256' not in panel
    before = (folder / 'report.json').read_bytes()
    with pytest.raises(FileExistsError):
        preview.build_preview(folder)
    assert (folder / 'report.json').read_bytes() == before


@pytest.mark.parametrize('field,value', [('heldout_run', True), ('through_year', 2011), ('calibrated', True)])
def test_panel_rejects_final_or_heldout_reports(tmp_path, field, value):
    folder = tmp_path / 'preview'
    report = preview.build_preview(folder)
    report[field] = value
    path = folder / 'report.json'
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='ending in 2010'):
        preview.read_panel(path)


def test_no_supplied_report_is_optional():
    assert preview.read_panel(None) is None
