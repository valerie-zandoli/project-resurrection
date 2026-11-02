import json
from pathlib import Path
import pytest
from report.history_preview import read_calibration

RECORD = Path(__file__).resolve().parents[1] / 'examples/development_calibration_20261029/calibration.json'

def test_saved_development_calibration_is_consistent():
    result = read_calibration(RECORD)
    assert result['chosen_mortality'] == 0.17
    assert result['settings'] == 41 and result['trials'] == 100
    assert result['within_tolerance'] is True

@pytest.mark.parametrize('field,value', [('heldout_run', True), ('through_year', 2011), ('chosen_mortality', .37)])
def test_invalid_or_heldout_record_is_refused(tmp_path, field, value):
    record = json.loads(RECORD.read_text());record[field] = value
    path = tmp_path / 'record.json';path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        read_calibration(path)
