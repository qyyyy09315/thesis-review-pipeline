"""Render the four-part undergraduate thesis review report."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from scorecard import build_scorecard, evidence_rows, render_html

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_context(run_dir: Path) -> dict:
    meta = _load_json(run_dir / "metadata.json")
    lint = _load_json(run_dir / "stage1" / "linter.json")
    cons = _load_json(run_dir / "agents" / "consolidator.json")
    a = _load_json(run_dir / "agents" / "agent_a_motivation.json")
    b = _load_json(run_dir / "agents" / "agent_b_methodology.json")
    c = _load_json(run_dir / "agents" / "agent_c_experiments.json")
    majors = cons.get("majors") or _harvest_findings([a, b, c], "major")
    minors = cons.get("minors") or _harvest_findings([a, b, c], "minor")
    if not majors:
        majors = _majors_from_lint(lint)
    if not minors:
        minors = _minors_from_lint(lint)
    grade = cons.get("grade") or _suggest_grade(lint, majors)
    summary = cons.get("contribution_summary") or (
        f"本稿题为《{meta.get('title') or lint.get('title') or '未命名'}》，"
        f"领域为{meta.get('field') or '未标注'}。"
        "当前审稿主要依据 Stage 1 机械预检与分审骨架，尚未完成全部人工深审。"
        f"预检检出未定义符号 {len(lint.get('undefined_symbols') or [])} 处、"
        f"过强断言 {len(lint.get('overclaims') or [])} 处、"
        f"结构缺口 {len(lint.get('structure_gaps') or [])} 项。"
    )
    reason = cons.get("grade_reason") or (
        "机械预检已暴露问题形式化、文献边界、消融与统计有效性缺口；"
        "在 Agent A/B/C 未填入实质性深审之前，不能按优秀论文标准定级。"
    )
    roadmap = _roadmap_or_default(cons.get("roadmap"))
    scorecard = cons.get("scorecard") or build_scorecard(lint)
    evidence_map = cons.get("evidence_map") or evidence_rows(majors, minors)
    return {
        "title": meta.get("title") or lint.get("title") or "未命名",
        "field": meta.get("field") or "未标注",
        "grade": grade,
        "contribution_summary": summary,
        "grade_reason": reason,
        "majors": majors,
        "minors": minors,
        "roadmap": roadmap,
        "scorecard": scorecard,
        "evidence_map": evidence_map,
        "lint": lint,
        "meta": meta,
    }


DEFAULT_ROADMAP = {
    "theory": [
        "补全问题形式化：给出输入/输出空间、符号表与目标函数各项含义。",
        "把“改进模块”写成可证伪机制，而不是模块清单。",
    ],
    "experiments": [
        "补充至少一组消融，证明每个改动的独立贡献。",
        "报告均值±方差或重复实验，并增加失效案例分析。",
    ],
    "writing": [
        "删除无数值支撑的“首次提出/显著提高/全面优于”。",
        "相关工作改为批判性对比，明确与最近 2–3 年 SOTA 的边界。",
    ],
}


def _roadmap_or_default(raw: object) -> dict:
    data = raw if isinstance(raw, dict) else {}
    out: dict[str, list] = {}
    for key, fallback in DEFAULT_ROADMAP.items():
        items = data.get(key)
        out[key] = items if isinstance(items, list) and items else list(fallback)
    return out


def _harvest_findings(payloads: list[dict], severity: str) -> list[dict]:
    found: list[dict] = []
    for payload in payloads:
        for item in payload.get("findings") or []:
            if str(item.get("severity", "")).lower() == severity and item.get("location"):
                found.append(item)
    return found


def _majors_from_lint(lint: dict) -> list[dict]:
    majors: list[dict] = []
    for gap in lint.get("structure_gaps") or []:
        if gap.get("key") in {"ablation", "related_work", "problem_formulation", "baseline"}:
            majors.append(
                {
                    "location": f"结构缺口/{gap.get('key')}",
                    "problem": gap.get("message"),
                    "basis": "优秀毕设与同行评审均要求问题可形式化、文献有边界、实验能隔离贡献。",
                    "action": "在对应章节补齐可核验的定义、对照表或消融表，而不是补一句口号。",
                }
            )
    dangling = [
        o
        for o in lint.get("overclaims") or []
        if not o.get("has_number") and not o.get("has_citation")
    ]
    if dangling:
        quote = dangling[0].get("quote", "")
        majors.append(
            {
                "location": f"摘要/结论 L{dangling[0].get('line')}",
                "problem": f"存在无量化支撑的过强断言，例如「{quote}」。",
                "basis": "主张强度必须被实验数字或引用锚定，否则构成 overclaim。",
                "action": "删除或改写为与证据匹配的表述，并在实验节给出对应指标。",
            }
        )
    return majors


def _minors_from_lint(lint: dict) -> list[dict]:
    minors: list[dict] = []
    for item in lint.get("undefined_symbols") or []:
        minors.append(
            {
                "location": f"公式 L{item.get('line')}",
                "problem": item.get("message"),
            }
        )
    for item in lint.get("overclaims") or []:
        if item.get("has_number") or item.get("has_citation"):
            minors.append(
                {
                    "location": f"L{item.get('line')}",
                    "problem": f"措辞偏满（{item.get('code')}）：{item.get('quote')}",
                }
            )
    for gap in lint.get("structure_gaps") or []:
        if gap.get("key") in {"failure_case", "variance"}:
            minors.append(
                {
                    "location": f"实验/{gap.get('key')}",
                    "problem": gap.get("message"),
                }
            )
    return minors


def _suggest_grade(lint: dict, majors: list) -> str:
    n_major = len(majors)
    n_undef = len(lint.get("undefined_symbols") or [])
    n_gap = len(lint.get("structure_gaps") or [])
    if n_major >= 3 or n_gap >= 4:
        return "退修"
    if n_major >= 1 or n_undef >= 2:
        return "及格"
    if n_gap:
        return "良好"
    return "良好"


def render_report(run_dir: Path) -> Path:
    ctx = collect_context(run_dir)
    markdown = _env().get_template("review_report.md.j2").render(**ctx)
    dest = run_dir / "review_report.md"
    dest.write_text(markdown, encoding="utf-8")
    html_dest = run_dir / "review_report.html"
    html_dest.write_text(render_html(ctx), encoding="utf-8")
    (run_dir / "stage3" / "scorecard.json").write_text(
        json.dumps(ctx.get("scorecard") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "stage3" / "render_context.json").write_text(
        json.dumps(ctx, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return dest
