from pathlib import Path

import json

import worklog
import thesis_review
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
    meta = json.loads((run_dirs[0] / "metadata.json").read_text(encoding="utf-8"))
    assert meta["grade"] == "待深审"
    assert meta["grade_suggested"] in {"退修", "及格", "良好"}


def test_ingest_cli_versioned_flag(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(worklog, "GLOBAL_LOG", tmp_path / "worklog.md")
    rc = main(
        [
            "ingest",
            str(FIXTURE),
            "--out-dir",
            str(tmp_path / "ingest"),
            "--versioned",
        ]
    )
    assert rc == 0
    files = list((tmp_path / "ingest").glob("sample_thesis-*.md"))
    assert files


def test_ledger_cli_add_close_list(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(worklog, "GLOBAL_LOG", tmp_path / "worklog.md")
    ledger_path = tmp_path / "ledger.json"
    rc = main(
        [
            "ledger",
            "add",
            "--severity",
            "minor",
            "--location",
            "5.6",
            "--problem",
            "遗留表述",
            "--run",
            "v20",
            "--ledger",
            str(ledger_path),
        ]
    )
    assert rc == 0
    assert "N-01" in capsys.readouterr().out
    rc = main(["ledger", "close", "--id", "N-01", "--run", "v21", "--ledger", str(ledger_path)])
    assert rc == 0
    rc = main(["ledger", "list", "--ledger", str(ledger_path)])
    out = capsys.readouterr().out
    assert "无匹配 issue" in out
    rc = main(["ledger", "list", "--all", "--ledger", str(ledger_path)])
    assert "N-01" in capsys.readouterr().out


def test_sanitize_cli_scrubs_global_log(tmp_path: Path, monkeypatch, capsys):
    log = tmp_path / "worklog.md"
    log.write_text(
        "源: F:/Temp/26实训-大四上第一次/初稿.docx 与 F:/FOR_PYTHON/project/26ECML/results/a.csv\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worklog, "GLOBAL_LOG", log)
    rc = main(["sanitize"])
    assert rc == 0
    cleaned = log.read_text(encoding="utf-8")
    assert "F:/" not in cleaned
    assert "papers/初稿.docx" in cleaned
    assert "工程侧/results/a.csv" in cleaned


def test_doctor_reports_missing_log(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(thesis_review, "ROOT", tmp_path)
    monkeypatch.setattr(worklog, "GLOBAL_LOG", tmp_path / "docs" / "worklog.md")
    run_dir = tmp_path / "runs" / "20260101-000000-x"
    (run_dir / "agents").mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps({"source": "papers/a.md", "ingest": "ingest/a.md"}),
        encoding="utf-8",
    )
    rc = main(["doctor"])
    assert rc == 1
    assert "无日志记录" in capsys.readouterr().out


def test_doctor_clean_workspace(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(thesis_review, "ROOT", tmp_path)
    log = tmp_path / "docs" / "worklog.md"
    log.parent.mkdir(parents=True)
    log.write_text("# 审稿工作日志\n\n## 2026-01-01\n\ninit-run x → 20260101-000000-x\n", encoding="utf-8")
    monkeypatch.setattr(worklog, "GLOBAL_LOG", log)
    run_dir = tmp_path / "runs" / "20260101-000000-x"
    (run_dir / "agents").mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps({"source": "papers/a.md", "ingest": "ingest/a.md"}),
        encoding="utf-8",
    )
    rc = main(["doctor"])
    assert rc == 0
    assert "一切正常" in capsys.readouterr().out


def _done_run(tmp_path: Path, monkeypatch, agent_c: dict) -> None:
    monkeypatch.setattr(thesis_review, "ROOT", tmp_path)
    log = tmp_path / "docs" / "worklog.md"
    log.parent.mkdir(parents=True)
    log.write_text("init-run → 20260101-000000-x\n", encoding="utf-8")
    monkeypatch.setattr(worklog, "GLOBAL_LOG", log)
    run_dir = tmp_path / "runs" / "20260101-000000-x"
    (run_dir / "agents").mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps({"source": "papers/a.md", "ingest": "ingest/a.md"}),
        encoding="utf-8",
    )
    (run_dir / "agents" / "consolidator.json").write_text(
        json.dumps({"status": "done", "majors": [], "minors": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_dir / "agents" / "agent_c_experiments.json").write_text(
        json.dumps(agent_c, ensure_ascii=False),
        encoding="utf-8",
    )


def test_doctor_flags_done_review_without_code_audit(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {"status": "done", "code_status": "pending", "code_correspondence": []},
    )
    rc = main(["doctor"])
    assert rc == 1
    assert "code_status" in capsys.readouterr().out


def test_doctor_accepts_legacy_done_review_without_code_field(tmp_path: Path, monkeypatch, capsys):
    _done_run(tmp_path, monkeypatch, {"status": "done", "findings": []})
    rc = main(["doctor"])
    assert rc == 0
    assert "一切正常" in capsys.readouterr().out


def test_doctor_accepts_matched_code_correspondence(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "quantitative_claims": True,
            "code_status": "checked",
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "paper_value": "0.812",
                    "code_ref": "results/main/foldmean.csv",
                    "code_value": "0.812",
                    "verdict": "match",
                }
            ],
        },
    )
    rc = main(["doctor"])
    assert rc == 0


def test_doctor_flags_mismatch_without_major(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "paper_value": "0.812",
                    "code_ref": "results/main/foldmean.csv",
                    "code_value": "0.790",
                    "verdict": "mismatch",
                }
            ],
        },
    )
    rc = main(["doctor"])
    assert rc == 1
    assert "mismatch" in capsys.readouterr().out
