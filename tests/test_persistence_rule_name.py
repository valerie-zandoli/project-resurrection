"""The persistence rule is named for what it checks:  a settled female and a breeding-age male in one patch.

The old name, breeding_pair_same_patch_at_end, left out the territory.  Synthetic fixtures only.
"""
import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
NEW = 'settled_breeding_pair_same_patch_at_end'
OLD = 'breeding_pair_same_patch_at_end'


def load(folder, name):
    return json.loads((ROOT / folder / name).read_text())


def input_with(rule):
    doc = copy.deepcopy(load('examples/handoffs', 'input.json'))
    doc['persistence_rule'] = rule
    return doc


def results_with(rule):
    doc = copy.deepcopy(load('examples/handoffs', 'results.json'))
    doc['config']['persistence_rule'] = rule
    return doc


def test_input_accepts_only_the_settled_rule_name():
    schema = load('schemas', 'input.schema.json')
    jsonschema.validate(input_with(NEW), schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(input_with(OLD), schema)


def test_results_config_accepts_only_the_settled_rule_name():
    schema = load('schemas', 'results.schema.json')
    jsonschema.validate(results_with(NEW), schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(results_with(OLD), schema)


def test_the_shipped_examples_use_the_settled_rule_name():
    assert load('examples/handoffs', 'input.json')['persistence_rule'] == NEW
    assert load('examples/handoffs', 'results.json')['config']['persistence_rule'] == NEW
