"""Five-dimension scorecard + issue-evidence map from Stage 1 lint.

Inspired by AliManjotho/open-reviewer scorecards and FanBroWell/AI-paper-reviewer
10-dimension red-flag tables, but mapped onto the undergraduate-thesis contract.
"""

from __future__ import annotations


DIMENSIONS: tuple[tuple[str, str], ...] = (
    ("problem", "问题定义"),
    ("literature", "文献综述"),
    ("method", "方法严密性"),
    ("experiment", "实验充分度"),
    ("writing", "写作规范"),
)


def _score_from_hits(hits: int, *, none: int = 5, one: int = 3, many: int = 1) -> int:
    if hits <= 0:
        return none
    if hits == 1:
        return one
    return many


def build_scorecard(lint: dict) -> list[dict]:
    gaps = {g.get("key"): g.get("message", "") for g in lint.get("structure_gaps") or []}
    undef = lint.get("undefined_symbols") or []
    dangling = [
        o
        for o in lint.get("overclaims") or []
        if not o.get("has_number") and not o.get("has_citation")
    ]
    exp_keys = [k for k in ("ablation", "baseline", "variance", "failure_case") if k in gaps]

    rows = [
        {
            "key": "problem",
            "name": "问题定义",
            "score": 1 if "problem_formulation" in gaps else 4,
            "note": gaps.get("problem_formulation") or "检出问题形式化信号。",
        },
        {
            "key": "literature",
            "name": "文献综述",
            "score": 1 if "related_work" in gaps else 4,
            "note": gaps.get("related_work") or "检出相关工作/综述信号。",
        },
        {
            "key": "method",
            "name": "方法严密性",
            "score": _score_from_hits(len(undef)),
            "note": (
                f"未定义符号 {len(undef)} 处："
                + "、".join(f"`{u.get('symbol')}`" for u in undef[:5])
                if undef
                else "公式符号均能在文中找到定义句。"
            ),
        },
        {
            "key": "experiment",
            "name": "实验充分度",
            "score": _score_from_hits(len(exp_keys), one=2, many=1),
            "note": (
                "缺口：" + "、".join(exp_keys)
                if exp_keys
                else "消融/基线/方差/失效案例信号均已出现。"
            ),
        },
        {
            "key": "writing",
            "name": "写作规范",
            "score": _score_from_hits(len(dangling)),
            "note": (
                f"无量化支撑的过强断言 {len(dangling)} 处。"
                if dangling
                else "未检出缺数字、缺引用的绝对化措辞。"
            ),
        },
    ]
    return rows


def evidence_rows(majors: list[dict], minors: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for item in majors:
        rows.append(
            {
                "severity": "Major",
                "location": item.get("location", ""),
                "problem": item.get("problem", ""),
                "action": item.get("action", ""),
            }
        )
    for item in minors:
        rows.append(
            {
                "severity": "Minor",
                "location": item.get("location", ""),
                "problem": item.get("problem", ""),
                "action": "",
            }
        )
    return rows


def html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(ctx: dict) -> str:
    title = html_escape(ctx.get("title", ""))
    field = html_escape(ctx.get("field", ""))
    grade = html_escape(ctx.get("grade", ""))
    summary = html_escape(ctx.get("contribution_summary", "")).replace("\n", "<br>")
    reason = html_escape(ctx.get("grade_reason", ""))
    score_rows = "".join(
        f"<tr><td>{html_escape(r['name'])}</td><td>{r['score']}/5</td>"
        f"<td>{html_escape(r['note'])}</td></tr>"
        for r in ctx.get("scorecard") or []
    )
    major_blocks = []
    for i, item in enumerate(ctx.get("majors") or [], start=1):
        major_blocks.append(
            "<li><p><strong>【定位】</strong>"
            f"{html_escape(item.get('location', ''))}</p>"
            "<p><strong>【具体问题】</strong>"
            f"{html_escape(item.get('problem', ''))}</p>"
            "<p><strong>【理论/学术依据】</strong>"
            f"{html_escape(item.get('basis', ''))}</p>"
            "<p><strong>【建议改进措施】</strong>"
            f"{html_escape(item.get('action', ''))}</p></li>"
        )
    if not major_blocks:
        if ctx.get("deep_done"):
            major_blocks.append("<li>（深审确认：无 Major。）</li>")
        else:
            major_blocks.append("<li>（深审尚未写入 Major，请先完成 Agent A/B/C 再 render。）</li>")
    minor_blocks = []
    for i, item in enumerate(ctx.get("minors") or [], start=1):
        minor_blocks.append(
            f"<li><strong>【{html_escape(item.get('location', ''))}】</strong>"
            f"{html_escape(item.get('problem', ''))}</li>"
        )
    if not minor_blocks:
        if ctx.get("deep_done"):
            minor_blocks.append("<li>（深审确认：无 Minor。）</li>")
        else:
            minor_blocks.append("<li>（暂无 Minor。）</li>")
    triage_rows = "".join(
        f"<tr><td>{html_escape(t.get('key', ''))}</td>"
        f"<td>{html_escape(t.get('verdict', ''))}</td>"
        f"<td>{html_escape(t.get('reason', ''))}</td></tr>"
        for t in ctx.get("linter_triage") or []
    )
    triage_section = ""
    if triage_rows:
        triage_section = (
            "<h4>Stage 1 机械预检对账（深审逐项复核）</h4>"
            "<table><thead><tr><th>预检项</th><th>判定</th><th>复核说明</th></tr></thead>"
            f"<tbody>{triage_rows}</tbody></table>"
        )
    ev_rows = "".join(
        f"<tr><td>{html_escape(r['severity'])}</td>"
        f"<td>{html_escape(r['location'])}</td>"
        f"<td>{html_escape(r['problem'])}</td></tr>"
        for r in ctx.get("evidence_map") or []
    )
    roadmap = ctx.get("roadmap") or {}
    def _ul(items: list) -> str:
        return "<ul>" + "".join(f"<li>{html_escape(x)}</li>" for x in items or []) + "</ul>"

    ledger_rows = "".join(
        f"<tr><td>{html_escape(it.get('id', ''))}</td>"
        f"<td>{html_escape(it.get('severity', ''))}</td>"
        f"<td>{html_escape(it.get('location', ''))}</td>"
        f"<td>{html_escape(it.get('problem', ''))}</td>"
        f"<td>{html_escape(it.get('first_seen', ''))}</td></tr>"
        for it in ctx.get("open_ledger") or []
    )
    ledger_section = ""
    if ledger_rows:
        ledger_section = (
            "<h4>跨轮遗留（docs/ledger.json 未闭环项）</h4>"
            "<table><thead><tr><th>ID</th><th>级别</th><th>定位</th><th>问题</th><th>首见</th></tr></thead>"
            f"<tbody>{ledger_rows}</tbody></table>"
        )

    ca = ctx.get("code_audit") or {}
    code_section = ""
    if ca.get("status"):
        code_rows = "".join(
            f"<tr><td>{html_escape(r['aspect'])}</td>"
            f"<td>{html_escape(r['claim'])}</td>"
            f"<td>{html_escape(r['paper'])}</td>"
            f"<td>{html_escape(r['code_ref'])}</td>"
            f"<td>{html_escape(r['code_value'])}</td>"
            f"<td>{html_escape(r['verdict'])}</td></tr>"
            for r in ca.get("rows") or []
        )
        head = f"对账状态：<code>{html_escape(ca.get('status', ''))}</code>"
        roots = "、".join(html_escape(x) for x in ca.get("roots") or [])
        if roots:
            head += f"；代码根目录：{roots}"
        note_html = f"<p>对账说明：{html_escape(ca.get('note', ''))}</p>" if ca.get("note") else ""
        table = ""
        if code_rows:
            table = (
                "<table><thead><tr><th>维度</th><th>主张</th><th>论文定位与摘引</th>"
                "<th>代码位置</th><th>代码取值</th><th>判定</th></tr></thead>"
                f"<tbody>{code_rows}</tbody></table>"
            )
        skipped_html = ""
        skipped = ca.get("skipped") or []
        if skipped:
            items = "".join(
                f"<li>{html_escape(s['label'])}——{html_escape(s['reason'])}</li>" for s in skipped
            )
            skipped_html = f"<p>未核验维度（已说明理由）：</p><ul>{items}</ul>"
        code_section = (
            "<h4>代码–论文对账（Agent C：数字 / 结构 / 超参 / 实验设计）</h4>"
            f"<p>{head}</p>{note_html}{table}{skipped_html}"
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>审稿报告 — {title}</title>
<style>
body {{ font-family: "Noto Serif SC", "Source Han Serif SC", serif; max-width: 880px; margin: 2rem auto; line-height: 1.6; color: #1a1a1a; }}
h1,h2,h3 {{ font-family: "Noto Sans SC", "Source Han Sans SC", sans-serif; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.95rem; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; vertical-align: top; }}
th {{ background: #f4f4f4; text-align: left; }}
.grade {{ font-size: 1.2rem; font-weight: 700; }}
</style>
</head>
<body>
<h1>高水平本科毕业设计审稿报告</h1>
<p>论文题目：{title}<br/>研究方向/专业领域：{field}<br/>整体定级：<span class="grade">{grade}</span></p>
<h3>一、 总体评价与学术定位（Executive Summary）</h3>
<p>{summary}</p>
<p>定级理由：{reason}</p>
<h4>五维评分卡</h4>
<table><thead><tr><th>维度</th><th>分数</th><th>依据</th></tr></thead>
<tbody>{score_rows}</tbody></table>
{code_section}
<h3>二、 实质性修改意见（Major Comments - 关乎学术严谨性与论证逻辑）</h3>
<ol>{"".join(major_blocks)}</ol>
<h3>三、 规范性与细节性修改意见（Minor Comments - 关乎格式、符号与表达）</h3>
<ol>{"".join(minor_blocks)}</ol>
{triage_section}
<h4>问题–证据表</h4>
<table><thead><tr><th>级别</th><th>定位</th><th>问题</th></tr></thead>
<tbody>{ev_rows}</tbody></table>
<h3>四、 二稿修改路线图与落地行动计划（Actionable Revision Roadmap）</h3>
<p><strong>理论与方法重塑（优先）</strong></p>
{_ul(roadmap.get("theory"))}
<p><strong>补充实验设计</strong></p>
{_ul(roadmap.get("experiments"))}
<p><strong>文本与结构精修</strong></p>
{_ul(roadmap.get("writing"))}
{ledger_section}
</body></html>
"""
