from scorecard import build_scorecard, evidence_rows, html_escape, render_html


def test_scorecard_penalizes_missing_ablation_and_overclaim():
    lint = {
        "structure_gaps": [
            {"key": "ablation", "message": "无消融"},
            {"key": "related_work", "message": "无综述"},
            {"key": "problem_formulation", "message": "无形式化"},
        ],
        "undefined_symbols": [{"symbol": "lambda", "line": 1, "message": "x"}],
        "overclaims": [
            {"has_number": False, "has_citation": False, "quote": "首次提出", "code": "OC1"}
        ],
    }
    rows = {r["key"]: r for r in build_scorecard(lint)}
    assert rows["problem"]["score"] == 1
    assert rows["literature"]["score"] == 1
    assert rows["experiment"]["score"] <= 2
    assert rows["writing"]["score"] <= 3
    assert rows["method"]["score"] <= 3


def test_html_escape_and_report_contains_scorecard():
    ctx = {
        "title": "A <B>",
        "field": "CS",
        "grade": "退修",
        "contribution_summary": "摘要",
        "grade_reason": "缺口",
        "scorecard": [{"name": "问题定义", "score": 1, "note": "无形式化"}],
        "majors": [
            {
                "location": "绪论",
                "problem": "未定义问题",
                "basis": "需形式化",
                "action": "补定义",
            }
        ],
        "minors": [{"location": "L1", "problem": "符号"}],
        "evidence_map": evidence_rows(
            [{"location": "绪论", "problem": "未定义问题", "action": "补定义"}],
            [{"location": "L1", "problem": "符号"}],
        ),
        "roadmap": {"theory": ["a"], "experiments": ["b"], "writing": ["c"]},
    }
    html = render_html(ctx)
    assert "A &lt;B&gt;" in html
    assert "五维评分卡" in html
    assert "问题–证据表" in html
    assert html_escape("<x>") == "&lt;x&gt;"
