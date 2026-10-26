"""Contract checks; examples are hand-authored and are not simulation results."""
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(kind, name):
    folder = "schemas" if kind == "schema" else "examples/handoffs"
    suffix = ".schema.json" if kind == "schema" else ".json"
    return json.loads((ROOT / folder / (name + suffix)).read_text())


@pytest.mark.parametrize("name", ["input", "results", "evaluation"])
def test_examples_match_contract(name):
    schema = load("schema", name)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(load("example", name), schema)


@pytest.mark.parametrize("field,value", [("seed", -1), ("duration_months", 0),
                                         ("start_month", 13), ("purpose", "historical")])
def test_invalid_inputs_fail(field, value):
    example = load("example", "input")
    example[field] = value
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, load("schema", "input"))


def test_missing_and_unknown_fields_fail():
    for change in ("missing", "unknown"):
        example = load("example", "input")
        if change == "missing":
            del example["seed"]
        else:
            example["disease_shock"] = True
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(example, load("schema", "input"))


def test_revision_limit():
    for name in ("results", "evaluation"):
        example = load("example", name)
        example["revision_round"] = 4
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(example, load("schema", name))


def test_sample_population_accounting():
    result = load("example", "results")
    assert result["run_id"] == result["config"]["run_id"]
    assert result["seed"] == result["config"]["seed"]
    assert len({a["id"] for a in result["final_animals"]}) == 20
    assert sum(a["sex"] == "female" for a in result["final_animals"]) == 10
    for previous, current in zip(result["history"], result["history"][1:]):
        assert current["population"] == previous["population"] + current["births"] - current["deaths"]
        assert current["population"] == current["females"] + current["males"]


@pytest.mark.parametrize("name,field", [("input", "parameters_sha256"), ("input", "sources_sha256"),
                                        ("evaluation", "parameters_sha256"), ("evaluation", "sources_sha256")])
def test_hash_fields_are_required_and_checked(name, field):
    schema = load("schema", name)
    missing = load("example", name)
    del missing[field]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(missing, schema)
    for bad in ("abc", "G" * 64, "A" * 64):
        wrong = load("example", name)
        wrong[field] = bad
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(wrong, schema)


def test_results_config_requires_the_hashes():
    result = load("example", "results")
    del result["config"]["parameters_sha256"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "results"))


@pytest.mark.parametrize("value", [None, "true", 0, 1])
def test_settled_must_be_boolean(value):
    result = load("example", "results")
    result["final_animals"][0]["settled"] = value
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "results"))


def test_settled_is_required_without_pair_only_fallback():
    result = load("example", "results")
    del result["final_animals"][0]["settled"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "results"))


@pytest.mark.parametrize("sex,alive", [("male", True), ("male", False), ("female", False)])
def test_only_living_females_can_hold_territories(sex, alive):
    result = load("example", "results")
    result["final_animals"][0].update(sex=sex, alive=alive, settled=True)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "results"))


def test_unsettled_living_female_and_dead_former_holder_are_valid_states():
    result = load("example", "results")
    result["final_animals"][0]["settled"] = False
    result["final_animals"][1].update(alive=False, settled=False)
    # Structural acceptance only; accounting and persisted need independent checks.
    jsonschema.validate(result, load("schema", "results"))


@pytest.mark.parametrize('version', ['1.0', '2.0'])
def test_old_results_version_is_rejected(version):
    result = load("example", "results")
    result["schema_version"] = version
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "results"))


def test_sample_has_five_settled_females_per_patch_and_no_settled_males():
    animals = load("example", "results")["final_animals"]
    for patch in ("A", "B"):
        assert sum(a["settled"] for a in animals if a["patch_id"] == patch) == 5
    assert all(not a["settled"] for a in animals if a["sex"] == "male")


def test_mixed_age_input_requires_both_bounds():
    result = load("example", "input")
    del result["initial_population"]["age_months_max"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "input"))


def test_unrecorded_parameter_override_is_rejected():
    result = load("example", "input")
    result["parameter_overrides"]["disease_mortality"] = 0.5
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, load("schema", "input"))


def test_settlement_rule_requires_input_contract_2_1():
    schema = load("schema", "input")
    example = load("example", "input")
    jsonschema.validate(example, schema)
    example["schema_version"] = "2.0"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, schema)


def test_results_3_1_requires_recorded_settlement_rule():
    schema = load("schema", "results")
    result = load("example", "results")
    jsonschema.validate(result, schema)
    del result["config"]["settlement_rule"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(result, schema)
