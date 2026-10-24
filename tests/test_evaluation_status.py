"""The evaluation schema ties the status to the issues and checks.

`pass` means all reported checks passed and no issues remain.  `revise` means issues need developer changes.
Before this rule the schema accepted a pass that listed an issue, so only the Evaluator's prompt held it.
"""
import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "evaluation.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "examples" / "handoffs" / "evaluation.json").read_text())
ISSUE = {"code": "UNKNOWN_SOURCE_KEY", "message": "Row 3 cites a key that is not in the registry.", "requested_change": "Use a registered key."}


def evaluation(status, issues=(), passed=True):
    doc = copy.deepcopy(EXAMPLE)
    doc["status"] = status
    doc["issues"] = list(issues)
    doc["checks"][0]["passed"] = passed
    return doc


def is_valid(doc):
    return jsonschema.Draft202012Validator(SCHEMA).is_valid(doc)


def test_a_clean_pass_is_accepted():
    assert is_valid(evaluation("pass"))


def test_a_pass_that_lists_an_issue_is_rejected():
    assert not is_valid(evaluation("pass", [ISSUE]))


def test_a_pass_with_a_failed_check_is_rejected():
    assert not is_valid(evaluation("pass", passed=False))


def test_a_revise_without_an_issue_is_rejected():
    assert not is_valid(evaluation("revise"))


def test_a_revise_with_an_issue_and_a_failed_check_is_accepted():
    assert is_valid(evaluation("revise", [ISSUE], passed=False))


@pytest.mark.parametrize("issues", [[], [ISSUE]])
def test_a_stop_may_carry_issues_or_none(issues):
    assert is_valid(evaluation("stop", issues, passed=False))
