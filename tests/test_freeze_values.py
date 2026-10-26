"""Tests for scripts/freeze_values.py:  the values come from the named checkout, nothing is changed, no key is used."""

import ast
import datetime
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("freeze_values", REPO / "scripts" / "freeze_values.py")
freeze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze)

from validators.handoff_hashes import file_sha256  # noqa: E402

FILES = {freeze.PARAMETERS: "name,value\nfood,4.6\n", freeze.SOURCES: "key,citation\nsource1,A paper\n"}


def git(path, *args):
    done = subprocess.run(["git", "-C", str(path), "-c", "user.name=Test", "-c", "user.email=test@example.com", *args],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "develop")
    for relative, text in FILES.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "start")
    return root


def run_main(root, *extra, capsys):
    code = freeze.main(["--root", str(root), *extra])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_the_values_come_from_the_named_checkout(checkout):
    values = freeze.collect(checkout)
    assert values["commit"] == git(checkout, "rev-parse", "HEAD") and len(values["commit"]) == 40
    assert values["branch"] == "develop" and values["dirty"] is False
    assert values["hashes"]["parameters_csv"] == file_sha256(checkout / freeze.PARAMETERS)
    assert values["hashes"]["sources_csv"] == file_sha256(checkout / freeze.SOURCES)
    assert values["python"].count(".") >= 1


def test_the_hash_is_the_harness_hash_so_a_crlf_checkout_agrees(checkout):
    expected = file_sha256(checkout / freeze.SOURCES)
    (checkout / freeze.SOURCES).write_bytes(FILES[freeze.SOURCES].replace("\n", "\r\n").encode())
    assert freeze.collect(checkout)["hashes"]["sources_csv"] == expected


def test_the_four_lines_of_the_pre_registration_are_printed(checkout, capsys):
    code, out, _ = run_main(checkout, "--runner", "Valerie Zandoli", capsys=capsys)
    values = freeze.collect(checkout)
    assert code == 0
    assert f"- The commit of the code that will run (hash):  {values['commit']}" in out
    assert f"`{freeze.PARAMETERS}` {values['hashes']['parameters_csv']}" in out
    assert f"`{freeze.SOURCES}` {values['hashes']['sources_csv']}" in out
    assert f"- The Python version:  {values['python']}" in out
    assert f"- The date and the name of the person who ran it:  {values['date']}, Valerie Zandoli" in out


def test_without_a_runner_the_name_stays_to_fill(checkout, capsys):
    _, out, _ = run_main(checkout, capsys=capsys)
    assert "TO FILL (name)" in out


def test_a_dirty_tree_prints_no_commit_and_exits_1(checkout, capsys):
    (checkout / freeze.PARAMETERS).write_text("changed\n", encoding="utf-8")
    code, out, err = run_main(checkout, capsys=capsys)
    assert code == 1 and out == "" and "uncommitted changes" in err


def test_allow_dirty_prints_the_values_with_a_warning(checkout, capsys):
    (checkout / "notes.txt").write_text("not committed\n", encoding="utf-8")
    code, out, _ = run_main(checkout, "--allow-dirty", capsys=capsys)
    assert code == 0 and "The commit of the code that will run" in out
    assert "WARNING:  The working tree has uncommitted changes" in out


def test_it_says_whether_head_is_the_tip_of_origin_develop(checkout):
    assert freeze.collect(checkout)["at_develop_tip"] is None
    git(checkout, "update-ref", "refs/remotes/origin/develop", "HEAD")
    assert freeze.collect(checkout)["at_develop_tip"] is True
    (checkout / "second.txt").write_text("more\n", encoding="utf-8")
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "second")
    values = freeze.collect(checkout)
    assert values["at_develop_tip"] is False
    assert any("not the tip of origin/develop" in text for text in freeze.warnings(values))


def test_another_python_version_gets_a_warning(checkout):
    values = freeze.collect(checkout, python_version="3.9.6")
    assert any("Python 3.9.6 is not 3.12" in text for text in freeze.warnings(values))
    assert not any("is not 3.12" in text for text in freeze.warnings(freeze.collect(checkout, python_version="3.12.4")))


def test_a_folder_that_is_not_a_git_checkout_exits_2(tmp_path, capsys):
    code, out, err = run_main(tmp_path, capsys=capsys)
    assert code == 2 and out == "" and "Cannot read the freeze values" in err


def test_a_missing_research_file_exits_2_and_names_it(checkout, capsys):
    (checkout / freeze.SOURCES).unlink()
    git(checkout, "add", "-A")
    git(checkout, "commit", "-q", "-m", "remove sources")
    code, _, err = run_main(checkout, capsys=capsys)
    assert code == 2 and freeze.SOURCES in err


def test_the_script_changes_nothing(checkout, capsys):
    before = sorted(path.relative_to(checkout).as_posix() for path in checkout.rglob("*") if ".git" not in path.parts)
    run_main(checkout, capsys=capsys)
    after = sorted(path.relative_to(checkout).as_posix() for path in checkout.rglob("*") if ".git" not in path.parts)
    assert before == after and git(checkout, "status", "--porcelain") == ""


def test_the_script_imports_no_network_or_model_library_and_never_runs_the_history_test():
    tree = ast.parse((REPO / "scripts" / "freeze_values.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"urllib", "http", "socket", "requests", "anthropic", "litellm", "simulation"}), imported
    assert imported <= {"argparse", "datetime", "platform", "subprocess", "sys", "pathlib", "validators"}, imported


def test_the_date_is_the_date_of_the_reading(checkout):
    now = datetime.datetime(2026, 10, 29, 19, 30, tzinfo=datetime.timezone.utc)
    values = freeze.collect(checkout, now=now)
    assert values["date"] == "2026-10-29" and values["read_at"].startswith("2026-10-29T19:30")
