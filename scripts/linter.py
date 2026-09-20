"""Stage 1 pre-flight linter for undergraduate thesis drafts.

Deterministic only: symbol table, dangling overclaims, structure gaps.
No subjective scoring.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

MATH_BLOCK = re.compile(r"\$\$([\s\S]*?)\$\$|\\\(([\s\S]*?)\\\)|\\\[([\s\S]*?)\\\]|\$([^$\n]+)\$")
LATEX_CMD = re.compile(r"\\[a-zA-Z]+")
SYMBOL_TOKEN = re.compile(
    r"(?:\\(?:lambda|alpha|beta|gamma|theta|phi|psi|omega|sigma|mu|nu|xi|eta|delta|epsilon|ell|mathcal\{[A-Za-z]+\}|mathrm\{[A-Za-z]+\}|hat\{[A-Za-z]+\}|bar\{[A-Za-z]+\}|tilde\{[A-Za-z]+\}|mathbf\{[A-Za-z]+\}|[A-Za-z]))"
    r"|[A-Za-z]_\{[^}]+\}"
    r"|[A-Za-z]_[A-Za-z0-9]"
    r"|\\[A-Za-z]+"
)
DEFINE_PATTERNS = (
    re.compile(r"(?:令|记|设|定义|其中|here\s+[A-Za-z\\]|let|denote|define)[^\n]{0,80}"),
    re.compile(r"([A-Za-z\\][A-Za-z0-9_\\{}\^]*)\s*(?:表示|为|is|denotes|stands for)"),
)
OVERCLAIM_PATTERNS: tuple[tuple[str, str], ...] = (
    ("OC1", r"首次提出"),
    ("OC2", r"实验证明"),
    ("OC3", r"显著提高"),
    ("OC4", r"全面优于"),
    ("OC5", r"效果很好"),
    ("OC6", r"广阔应用前景"),
    ("OC7", r"state[- ]of[- ]the[- ]art"),
    ("OC8", r"significantly (?:improve|outperform)"),
    ("OC9", r"we (?:first|for the first time) propose"),
)
STRUCTURE_SIGNALS: dict[str, tuple[str, ...]] = {
    "related_work": (
        "相关工作", "文献综述", "研究现状", "related work",
        "国内外研究", "研究进展", "已有研究", "近年来", "学者提出",
    ),
    "ablation": (
        "消融", "ablation",
        "去除", "移除", "单独使用", "仅使用", "各模块", "变体", "模块贡献",
    ),
    "baseline": (
        "基线", "baseline", "对比方法", "对比算法", "对比实验",
        "对照组", "传统方法", "现有方法", "主流方法", "常用于",
    ),
    "failure_case": (
        "失效", "失败案例", "failure case", "limitation", "局限",
        "误判", "误报", "漏检", "异常情况", "错误案例",
    ),
    "variance": (
        "方差", "标准差", "误差棒", "error bar", "std", "±",
        "均值", "平均准确率", "重复实验", "交叉验证", "折平均", "稳定性", "置信区间",
    ),
    "problem_formulation": (
        "形式化", "问题定义", "输入输出", "problem formulation",
        "问题描述", "任务定义", "输入为", "输出为", "建模", "定义如下", "研究内容",
    ),
}
COMMON_DEFINED = {
    "x",
    "y",
    "n",
    "N",
    "t",
    "i",
    "j",
    "k",
    "m",
    "d",
    "L",
    "f",
    "e",
}


@dataclass
class SymbolIssue:
    symbol: str
    line: int
    message: str


@dataclass
class OverclaimIssue:
    code: str
    line: int
    quote: str
    has_number: bool
    has_citation: bool
    message: str


@dataclass
class StructureGap:
    key: str
    message: str


@dataclass
class LintResult:
    title: str
    n_chars: int
    n_lines: int
    defined_symbols: list[str] = field(default_factory=list)
    undefined_symbols: list[SymbolIssue] = field(default_factory=list)
    overclaims: list[OverclaimIssue] = field(default_factory=list)
    structure_gaps: list[StructureGap] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "n_chars": self.n_chars,
            "n_lines": self.n_lines,
            "defined_symbols": self.defined_symbols,
            "undefined_symbols": [asdict(x) for x in self.undefined_symbols],
            "overclaims": [asdict(x) for x in self.overclaims],
            "structure_gaps": [asdict(x) for x in self.structure_gaps],
            "headings": self.headings,
            "blocker_count": len(self.undefined_symbols)
            + sum(1 for o in self.overclaims if not o.has_number),
            "major_hint_count": len(self.structure_gaps),
        }


def _normalize_symbol(raw: str) -> str:
    text = raw.strip()
    text = text.replace("\\", "")
    text = re.sub(r"[{}]", "", text)
    text = text.replace("hat", "").replace("bar", "").replace("tilde", "")
    text = text.replace("mathcal", "").replace("mathrm", "").replace("mathbf", "")
    return text.strip()


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("\\title{"):
            return stripped[7:].rstrip("}").strip()
    return "untitled"


def _headings(text: str) -> list[str]:
    found: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            found.append(re.sub(r"^#+\s*", "", line).strip())
        elif line.startswith("\\chapter") or line.startswith("\\section"):
            found.append(line.strip())
    return found


def _defined_symbols(text: str) -> set[str]:
    defined: set[str] = set(COMMON_DEFINED)
    for pattern in DEFINE_PATTERNS:
        for match in pattern.finditer(text):
            chunk = match.group(0)
            for token in SYMBOL_TOKEN.findall(chunk):
                normalized = _normalize_symbol(token)
                if normalized:
                    defined.add(normalized)
            if match.lastindex:
                extra = match.group(1)
                if extra:
                    defined.add(_normalize_symbol(extra))
    # Explicit "令 $L_{ce}$ 表示" style
    for match in re.finditer(
        r"(?:令|记|设|其中)\s*\$([^$]+)\$\s*(?:表示|为|是)",
        text,
    ):
        defined.add(_normalize_symbol(match.group(1)))
    return {s for s in defined if s}


def _math_symbols(text: str) -> list[tuple[str, int]]:
    lines = text.splitlines()
    hits: list[tuple[str, int]] = []
    for i, line in enumerate(lines, start=1):
        for match in MATH_BLOCK.finditer(line):
            blob = next(g for g in match.groups() if g)
            blob = LATEX_CMD.sub(lambda m: m.group(0), blob)
            for token in SYMBOL_TOKEN.findall(blob):
                hits.append((_normalize_symbol(token), i))
    # also scan display blocks spanning lines
    for match in re.finditer(r"\$\$([\s\S]*?)\$\$", text):
        blob = match.group(1)
        line_no = text[: match.start()].count("\n") + 1
        for token in SYMBOL_TOKEN.findall(blob):
            hits.append((_normalize_symbol(token), line_no))
    return [(s, n) for s, n in hits if s and not s.isdigit()]


def _overclaims(text: str) -> list[OverclaimIssue]:
    issues: list[OverclaimIssue] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        for code, pattern in OVERCLAIM_PATTERNS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                has_number = bool(re.search(r"\d+(?:\.\d+)?\s*%|\d+\.\d+", line))
                has_citation = bool(
                    re.search(r"\[[^\]]+\]|\\cite\{|（[^）]*\d{4}[^）]*）", line)
                )
                issues.append(
                    OverclaimIssue(
                        code=code,
                        line=i,
                        quote=line.strip()[:180],
                        has_number=has_number,
                        has_citation=has_citation,
                        message=(
                            "断言含绝对化措辞，但本句缺少数值量化或文献索引。"
                            if not has_number and not has_citation
                            else "断言含绝对化措辞，请核对证据强度是否匹配。"
                        ),
                    )
                )
    return issues


NEGATION_MARKERS = ("未曾", "未能", "未做", "未报", "未分析", "未含", "未见", "未设", "未给", "未进行", "未开展", "没有", "缺乏", "尚未", "并不", "未")


def _needle_starts(text: str, needle: str) -> list[int]:
    lowered = text.lower()
    target = needle.lower()
    if re.fullmatch(r"[a-z0-9+\-]+", target):
        return [m.start() for m in re.finditer(rf"\b{re.escape(target)}\b", lowered)]
    starts: list[int] = []
    start = 0
    while True:
        idx = lowered.find(target, start)
        if idx < 0:
            return starts
        starts.append(idx)
        start = idx + max(len(target), 1)


def _is_negated(prefix: str) -> bool:
    compact = re.sub(r"\s+", "", prefix)
    return any(marker in compact for marker in NEGATION_MARKERS)


def _has_positive_signal(text: str, needles: tuple[str, ...]) -> bool:
    """True only if a keyword appears outside a local negation window."""
    for needle in needles:
        for idx in _needle_starts(text, needle):
            prefix = text[max(0, idx - 12) : idx]
            if not _is_negated(prefix):
                return True
    return False


def _structure_gaps(text: str) -> list[StructureGap]:
    gaps: list[StructureGap] = []
    labels = {
        "related_work": "未见独立的相关工作/文献综述章节信号，综述可能被压缩为罗列或缺失。",
        "ablation": "全文未出现消融实验信号，无法证明各模块独立贡献。",
        "baseline": "未检出基线/对比方法表述，实验对照可能不充分。",
        "failure_case": "未检出失效案例或局限性分析。",
        "variance": "未检出方差/误差棒/显著性表述。",
        "problem_formulation": "未检出问题形式化/输入输出定义信号。",
    }
    for key, needles in STRUCTURE_SIGNALS.items():
        if not _has_positive_signal(text, needles):
            gaps.append(StructureGap(key=key, message=labels[key]))
    return gaps


def lint_text(text: str) -> LintResult:
    defined = _defined_symbols(text)
    used = _math_symbols(text)
    seen: set[str] = set()
    undefined: list[SymbolIssue] = []
    for symbol, line in used:
        if symbol in defined or symbol in seen:
            continue
        if len(symbol) == 1 and symbol in COMMON_DEFINED:
            continue
        # skip pure latex layout tokens
        if symbol in {"left", "right", "frac", "sum", "prod", "int", "min", "max"}:
            continue
        seen.add(symbol)
        undefined.append(
            SymbolIssue(
                symbol=symbol,
                line=line,
                message=f"公式中出现符号 `{symbol}`，全文未见显式定义。",
            )
        )
    return LintResult(
        title=_extract_title(text),
        n_chars=len(text),
        n_lines=text.count("\n") + 1,
        defined_symbols=sorted(defined),
        undefined_symbols=undefined,
        overclaims=_overclaims(text),
        structure_gaps=_structure_gaps(text),
        headings=_headings(text),
    )


def lint_file(path: Path) -> LintResult:
    return lint_text(path.read_text(encoding="utf-8"))


def render_markdown(result: LintResult) -> str:
    data = result.to_dict()
    lines = [
        f"# Stage 1 预检 — {result.title}",
        "",
        f"- 字符数：{result.n_chars}",
        f"- 行数：{result.n_lines}",
        f"- 未定义符号：{len(result.undefined_symbols)}",
        f"- 悬空/过强断言：{len(result.overclaims)}",
        f"- 结构缺口：{len(result.structure_gaps)}",
        "",
        "## 标题层级",
    ]
    lines.extend(f"- {h}" for h in result.headings or ["（未检出标题）"])
    lines += ["", "## 未定义符号"]
    if result.undefined_symbols:
        lines.extend(
            f"- L{item.line} `{item.symbol}`：{item.message}"
            for item in result.undefined_symbols
        )
    else:
        lines.append("- 无")
    lines += ["", "## 悬空断言"]
    if result.overclaims:
        for item in result.overclaims:
            flag = "有数字" if item.has_number else "缺数字"
            cite = "有引用" if item.has_citation else "缺引用"
            lines.append(
                f"- L{item.line} [{item.code}] ({flag}/{cite}) {item.quote} — {item.message}"
            )
    else:
        lines.append("- 无")
    lines += ["", "## 结构缺口"]
    if result.structure_gaps:
        lines.extend(f"- `{g.key}`：{g.message}" for g in result.structure_gaps)
    else:
        lines.append("- 无")
    lines += ["", "```json", json.dumps(data, ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 1 thesis pre-flight linter")
    parser.add_argument("file", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = lint_file(args.file)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
