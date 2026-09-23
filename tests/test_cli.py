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
    agent_c = json.loads(
        (run_dirs[0] / "agents" / "agent_c_experiments.json").read_text(encoding="utf-8")
    )
    assert agent_c["code_status"] == "pending"
    assert agent_c["aspects_skipped"] == {}


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
            "aspects_skipped": {
                "architecture": "未提供模型定义文件",
                "hyperparameter": "未提供训练配置",
                "design": "未提供数据划分脚本",
            },
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "aspect": "number",
                    "paper_ref": "5.3 表5.1",
                    "paper_quote": "macro-F1 0.812±0.01",
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
            "aspects_skipped": {
                "architecture": "未提供模型定义文件",
                "hyperparameter": "未提供训练配置",
                "design": "未提供数据划分脚本",
            },
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "aspect": "number",
                    "paper_ref": "5.3 表5.1",
                    "paper_quote": "macro-F1 0.812±0.01",
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


_FULL_SKIP = {
    "number": "无定量结果",
    "architecture": "无结构描述",
    "hyperparameter": "无训练配置",
    "design": "无实验设计",
}


def test_doctor_flags_row_missing_aspect_and_paper_ref(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "aspects_skipped": dict(_FULL_SKIP),
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
    assert rc == 1
    out = capsys.readouterr().out
    assert "缺 aspect" in out
    assert "缺 paper_ref" in out


def test_doctor_flags_illegal_aspect(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "aspects_skipped": dict(_FULL_SKIP),
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "aspect": "loss",
                    "paper_ref": "5.3 表5.1",
                    "paper_value": "0.812",
                    "code_ref": "results/main/foldmean.csv",
                    "code_value": "0.812",
                    "verdict": "match",
                }
            ],
        },
    )
    rc = main(["doctor"])
    assert rc == 1
    assert "aspect 非法" in capsys.readouterr().out


def test_doctor_flags_uncovered_aspects(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "aspect": "number",
                    "paper_ref": "5.3 表5.1",
                    "paper_value": "0.812",
                    "code_ref": "results/main/foldmean.csv",
                    "code_value": "0.812",
                    "verdict": "match",
                }
            ],
        },
    )
    rc = main(["doctor"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "未对账维度 architecture" in out
    assert "未对账维度 hyperparameter" in out
    assert "未对账维度 design" in out


def test_doctor_flags_skipped_without_reason(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "aspects_skipped": {
                "architecture": "",
                "hyperparameter": "无训练配置",
                "design": "无实验设计",
            },
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "aspect": "number",
                    "paper_ref": "5.3 表5.1",
                    "paper_value": "0.812",
                    "code_ref": "results/main/foldmean.csv",
                    "code_value": "0.812",
                    "verdict": "match",
                }
            ],
        },
    )
    rc = main(["doctor"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "aspects_skipped[architecture] 未写跳过理由" in out
    assert "未对账维度 architecture" in out


def test_doctor_accepts_aspects_skipped_reasons(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "aspects_skipped": {
                "architecture": "未提供模型定义文件",
                "hyperparameter": "未提供训练配置",
                "design": "未提供数据划分脚本",
            },
            "code_correspondence": [
                {
                    "claim": "表5.1 macro-F1",
                    "aspect": "number",
                    "paper_ref": "5.3 表5.1",
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
    assert "一切正常" in capsys.readouterr().out


def test_doctor_quantitative_false_skips_number_aspect(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "quantitative_claims": False,
            "code_status": "checked",
            "aspects_skipped": {
                "hyperparameter": "理论稿无训练配置",
                "design": "理论稿无实验设计",
            },
            "code_correspondence": [
                {
                    "claim": "算法1 堆叠层数 L=3",
                    "aspect": "architecture",
                    "paper_ref": "4.1 算法1",
                    "paper_quote": "堆叠 L=3 层",
                    "paper_value": "L=3",
                    "code_ref": "src/algo/stack.py",
                    "code_value": "num_layers=3",
                    "verdict": "match",
                }
            ],
        },
    )
    rc = main(["doctor"])
    assert rc == 0
    assert "一切正常" in capsys.readouterr().out


def test_doctor_flags_mismatch_without_quote(tmp_path: Path, monkeypatch, capsys):
    _done_run(
        tmp_path,
        monkeypatch,
        {
            "status": "done",
            "code_status": "checked",
            "aspects_skipped": {
                "architecture": "未提供模型定义文件",
                "hyperparameter": "未提供训练配置",
                "design": "未提供数据划分脚本",
            },
            "code_correspondence": [
                {
                    "claim": "训练学习率 1e-3",
                    "aspect": "hyperparameter",
                    "paper_ref": "5.2 表5.3",
                    "paper_value": "lr=1e-3",
                    "code_ref": "configs/main.yaml",
                    "code_value": "lr=3e-4",
                    "verdict": "mismatch",
                }
            ],
            "findings": [
                {
                    "severity": "major",
                    "location": "5.2 表5.3",
                    "problem": "论文学习率与代码配置不一致。",
                }
            ],
        },
    )
    cons_path = tmp_path / "runs" / "20260101-000000-x" / "agents" / "consolidator.json"
    cons = json.loads(cons_path.read_text(encoding="utf-8"))
    cons["majors"] = [
        {
            "location": "5.2 表5.3",
            "problem": "论文所述超参与代码配置不一致。",
            "basis": "可复现性",
            "action": "统一论文与配置。",
        }
    ]
    cons_path.write_text(json.dumps(cons, ensure_ascii=False), encoding="utf-8")
    rc = main(["doctor"])
    assert rc == 1
    assert "paper_quote" in capsys.readouterr().out
