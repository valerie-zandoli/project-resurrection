"""The files that the harness validates are the files that the agents read:  the snapshot."""

from pathlib import Path

from harness import run_case as run_case_module
from harness.run_case import run_case

OPTIONS = dict(seed=3, months=6, food=4.6, area=50)


def test_the_snapshot_is_what_gets_validated(tmp_path, monkeypatch):
    seen = []
    real = run_case_module.validate_parameters

    def spy(*paths):
        seen.extend(Path(path) for path in paths)
        return real(*paths)

    monkeypatch.setattr(run_case_module, "validate_parameters", spy)
    run_case(tmp_path / "case", options=OPTIONS)
    assert seen and all((tmp_path / "case" / "snapshot") in path.parents for path in seen)


def test_a_missing_research_file_rejects_the_case_instead_of_crashing(tmp_path):
    source = tmp_path / "source"
    (source / "data" / "parameters").mkdir(parents=True)  # the folder exists; the research files do not
    result = run_case(tmp_path / "case", options=OPTIONS, source_root=source)
    assert result.status == "rejected" and "research files" in result.reason
    assert (tmp_path / "case" / "case.json").exists()
