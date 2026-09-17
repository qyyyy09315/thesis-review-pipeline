from pathlib import Path

import worklog
from thesis_review import main

FIXTURE = Path(__file__).parent / "fixtures" / "sample_thesis.md"


def test_init_run_cli(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(worklog, "GLOBAL_LOG", tmp_path / "worklog.md")
    local = tmp_path / "paper.md"
    local.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    rc = main(
        [
            "init-run",
            str(local),
            "--title",
            "样例",
            "--field",
            "计算机",
            "--runs-dir",
            str(tmp_path / "runs"),
            "--ingest-dir",
            str(tmp_path / "ingest"),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "review_report.md" in out
    run_dirs = list((tmp_path / "runs").iterdir())
    assert run_dirs
    report = (run_dirs[0] / "review_report.md").read_text(encoding="utf-8")
    assert "总体评价与学术定位" in report
    assert (run_dirs[0] / "stage1" / "linter.json").exists()
