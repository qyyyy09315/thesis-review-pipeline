from pathlib import Path

import worklog
from thesis_review import main


def test_item_add_requires_mention(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(worklog, "GLOBAL_LOG", tmp_path / "worklog.md")
    rc = main(
        [
            "item",
            "add",
            "--problem",
            "没有点名",
            "--delivery",
            str(tmp_path / "delivery.json"),
        ]
    )
    assert rc == 1
    assert "@" in capsys.readouterr().err


def test_overview_mentions_owner_and_decision(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(worklog, "GLOBAL_LOG", tmp_path / "worklog.md")
    path = str(tmp_path / "delivery.json")
    assert (
        main(
            [
                "item",
                "add",
                "--type",
                "claim",
                "--track",
                "algorithm",
                "--mention",
                "@qyyyy09315",
                "--problem",
                "修复后精度还没有",
                "--delivery",
                path,
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "project",
                "set",
                "--decision",
                "是否重跑 12k",
                "--unverified",
                "新算法精度",
                "--next-action",
                "先冻结修复版",
                "--delivery",
                path,
            ]
        )
        == 0
    )
    assert main(["overview", "--delivery", path]) == 0
    out = capsys.readouterr().out
    assert "R-01" in out
    assert "@qyyyy09315" in out
    assert "是否重跑 12k" in out
    assert "不表示毕设可以放行" in out


def test_pr_check_cli_rejects_body_without_mention(capsys):
    rc = main(
        [
            "pr-check",
            "--title",
            "feat: 示例",
            "--body",
            "## 摘要\n\n## 动机\n\n## 改动\n\n## 测试\n\n## 决定\n\n",
        ]
    )
    assert rc == 1
    assert "@name" in capsys.readouterr().out


def test_scope_cli_keeps_unchanged_areas(capsys):
    rc = main(["scope", "--changed", "scripts/ingest.py"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "pytest tests/test_ingest.py" in out
    assert "依赖未变" in out
