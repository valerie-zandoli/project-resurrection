"""The code-graded evidence question:  the Researcher names the low rows and the recorded conflicts,
and code compares those names with the evidence file.  The grade is recorded beside the verdict and
never changes it."""

import json
from pathlib import Path

import pytest

from harness.provider import FakeProvider
from harness.three_role_preview import (RESEARCHER_TASK, grade_evidence_answer, run_three_role_case,
                                        scripted_providers)
from harness.snapshot import RESEARCH_FILES
from simulation.model import REPO
from validators.evidence_gate import check_evidence

OPTIONS = dict(seed=7, months=12, food=4.6, area=50)
READS = [dict(name="read_research", arguments=dict(key=key)) for key in ("parameters", "sources", "evidence")]


def report():
    errors, found = check_evidence(REPO, *(REPO / name for name in RESEARCH_FILES), "pilot")
    assert not errors
    return found


def answer(low, conflicts):
    return f"Short summary.\nLOW: {', '.join(low) or 'none'}\nCONFLICTS: {', '.join(conflicts) or 'none'}"


def test_the_real_evidence_file_has_low_rows_and_conflicts_to_name():
    found = report()
    assert len(found["low"]) > 1 and len(found["conflicts"]) > 1   # so a lazy answer cannot pass


def test_a_correct_answer_passes():
    found = report()
    check = grade_evidence_answer(answer(found["low"], list(found["conflicts"])), found)
    assert check["pass"] and check["answered"]
    assert check["low"]["missing"] == [] and check["conflicts"]["invented"] == []


def test_a_missing_low_row_fails_and_is_named():
    found = report()
    check = grade_evidence_answer(answer(found["low"][1:], list(found["conflicts"])), found)
    assert not check["pass"] and check["low"]["missing"] == [found["low"][0]]


def test_an_invented_conflict_fails_and_is_named():
    found = report()
    check = grade_evidence_answer(answer(found["low"], list(found["conflicts"]) + ["no_such_parameter"]), found)
    assert not check["pass"] and check["conflicts"]["invented"] == ["no_such_parameter"]


def test_none_for_conflicts_fails_when_the_file_records_conflicts():
    found = report()
    check = grade_evidence_answer(answer(found["low"], []), found)
    assert not check["pass"] and check["conflicts"]["missing"] == sorted(found["conflicts"])


def test_an_answer_without_the_two_lines_is_not_answered():
    check = grade_evidence_answer("I read the tables and they look fine.", report())
    assert not check["answered"] and not check["pass"]


def test_markdown_bold_and_backticks_around_the_lines_and_names_are_accepted():
    found = report()
    text = ("Summary.\n**LOW:** " + ", ".join(f"`{name}`" for name in found["low"])
            + "\n- CONFLICTS: " + ", ".join(found["conflicts"]))
    assert grade_evidence_answer(text, found)["pass"]


def test_the_task_asks_for_a_short_answer_that_ends_in_the_two_lines():
    assert "at most 150 words" in RESEARCHER_TASK
    assert "\nLOW:" in RESEARCHER_TASK and "\nCONFLICTS:" in RESEARCHER_TASK


def test_the_scripted_run_records_a_passing_grade_in_the_researcher_file_and_the_manifest(tmp_path):
    result = run_three_role_case(tmp_path / "case", providers=scripted_providers(), options=OPTIONS)
    assert result.status == "pass"
    researcher = json.loads((tmp_path / "case/round_0/researcher.json").read_text())
    manifest = json.loads((tmp_path / "case/pipeline.json").read_text())
    assert researcher["evidence_check"]["pass"] is True
    assert manifest["evidence_read_check"] == researcher["evidence_check"]


def test_a_wrong_answer_is_recorded_as_a_failed_grade_but_the_verdict_still_stands(tmp_path):
    providers = scripted_providers()
    providers["researcher"] = FakeProvider([dict(text="", tool_calls=READS),
                                            dict(text="Looks fine.\nLOW: none\nCONFLICTS: none")])
    result = run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    assert result.status == "pass"                                      # the code verdict is unchanged
    check = json.loads((tmp_path / "case/round_0/researcher.json").read_text())["evidence_check"]
    assert check["pass"] is False and check["low"]["missing"] == sorted(report()["low"])


def test_the_researcher_task_text_reaches_the_model(tmp_path):
    providers = scripted_providers()
    researcher = providers["researcher"]
    run_three_role_case(tmp_path / "case", providers=providers, options=OPTIONS)
    first_user_message = researcher.calls[0]["messages"][0]["content"]
    assert first_user_message == RESEARCHER_TASK
