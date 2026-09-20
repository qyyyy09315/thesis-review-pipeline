import json
from pathlib import Path

from ingest import ingest_file, slugify
from linter import lint_file, render_markdown
from render import render_report
from workspace import create_run

FIXTURE = Path(__file__).parent / "fixtures" / "sample_thesis.md"

REQUIRED_HEADINGS = [
    "### 一、 总体评价与学术定位（Executive Summary）",
    "### 二、 实质性修改意见（Major Comments - 关乎学术严谨性与论证逻辑）",
    "### 三、 规范性与细节性修改意见（Minor Comments - 关乎格式、符号与表达）",
    "### 四、 二稿修改路线图与落地行动计划（Actionable Revision Roadmap）",
]


def test_init_like_render_has_four_sections(tmp_path: Path):
    ingest_md = ingest_file(FIXTURE, tmp_path / "ingest")
    run_dir = create_run(
        paper_src=FIXTURE,
        ingest_md=ingest_md,
        slug=slugify(FIXTURE.stem),
        title="样例论文",
        field="计算机科学与技术",
        runs_dir=tmp_path / "runs",
    )
    lint = lint_file(run_dir / "paper.md")
    (run_dir / "stage1" / "linter.json").write_text(
        json.dumps(lint.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "stage1" / "linter.md").write_text(render_markdown(lint), encoding="utf-8")
    report = render_report(run_dir)
    text = report.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in text
    assert "【定位】" in text
    assert any(g in text for g in ("退修", "及格", "良好", "优秀"))
    assert "补全问题形式化" in text
    assert "补充至少一组消融" in text
    assert "五维评分卡" in text
    assert "问题–证据表" in text
    html = (run_dir / "review_report.html").read_text(encoding="utf-8")
    assert "五维评分卡" in html
    assert (run_dir / "stage3" / "scorecard.json").exists()


def _prepare_run(tmp_path: Path) -> Path:
    ingest_md = ingest_file(FIXTURE, tmp_path / "ingest")
    run_dir = create_run(
        paper_src=FIXTURE,
        ingest_md=ingest_md,
        slug=slugify(FIXTURE.stem),
        title="样例论文",
        field="计算机科学与技术",
        runs_dir=tmp_path / "runs",
    )
    lint = lint_file(run_dir / "paper.md")
    (run_dir / "stage1" / "linter.json").write_text(
        json.dumps(lint.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return run_dir


def test_done_consolidator_empty_majors_is_respected(tmp_path: Path):
    """status=done 且 majors=[] 表示深审确认无，机械兜底不得回填假 Major。"""
    run_dir = _prepare_run(tmp_path)
    cons_path = run_dir / "agents" / "consolidator.json"
    cons = json.loads(cons_path.read_text(encoding="utf-8"))
    cons.update(
        {
            "status": "done",
            "grade": "良好",
            "contribution_summary": "深审摘要。",
            "grade_reason": "复核通过。",
        }
    )
    cons_path.write_text(json.dumps(cons, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_report(run_dir)
    text = report.read_text(encoding="utf-8")
    assert "深审确认：无 Major。" in text
    assert "结构缺口/" not in text
    html = (run_dir / "review_report.html").read_text(encoding="utf-8")
    assert "深审确认：无 Major" in html


def test_pending_consolidator_still_falls_back(tmp_path: Path):
    """status=pending 时保持旧契约：结构缺口以机械 Major 形式进入初稿报告。"""
    run_dir = _prepare_run(tmp_path)
    report = render_report(run_dir)
    text = report.read_text(encoding="utf-8")
    assert "结构缺口/" in text
    assert "深审确认" not in text


def test_linter_triage_surface(tmp_path: Path):
    """consolidator.linter_triage 应出现在报告的预检对账表中。"""
    run_dir = _prepare_run(tmp_path)
    cons_path = run_dir / "agents" / "consolidator.json"
    cons = json.loads(cons_path.read_text(encoding="utf-8"))
    cons["linter_triage"] = [
        {"key": "problem_formulation", "verdict": "reject", "reason": "5.1 已定义输入输出。"}
    ]
    cons_path.write_text(json.dumps(cons, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_report(run_dir)
    text = report.read_text(encoding="utf-8")
    assert "机械预检对账" in text
    assert "problem_formulation" in text
