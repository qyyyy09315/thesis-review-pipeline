"""Append-only work log for the thesis review workspace."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_LOG = ROOT / "docs" / "worklog.md"

ABS_PATH_RE = re.compile(r"[A-Za-z]:[/\\][^\s，。；、）】」'\"`)`|]*")


def scrub_local_paths(text: str) -> str:
    """Rewrite host absolute paths into portable, privacy-safe references.

    - 工程侧路径（.../26ECML/...）→ `工程侧/<仓库内相对路径>`
    - 论文源 `初稿.docx` → `papers/初稿.docx`
    - 仓库自身路径 → 仓库内相对路径
    - 其余盘符路径 → `<本地路径>`（不应出现；出现即需人工复核）
    """

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        norm = raw.replace("\\", "/").rstrip("/.,;")
        lowered = norm.lower()
        name = norm.split("/")[-1]
        if "26ecml" in lowered:
            idx = lowered.find("26ecml")
            tail = norm[idx + len("26ecml"):].lstrip("/")
            return f"工程侧/{tail}" if tail else "工程侧"
        if name == "初稿.docx":
            return "papers/初稿.docx"
        if "审稿工作区" in norm:
            idx = norm.find("审稿工作区")
            tail = norm[idx + len("审稿工作区"):].lstrip("/")
            return tail or "."
        return "<本地路径>"

    return ABS_PATH_RE.sub(repl, text)


def append_worklog(message: str, run_dir: Path | None = None, extra: str = "") -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    block = f"## {stamp}\n\n{message.strip()}\n"
    if extra.strip():
        block += f"\n{extra.strip()}\n"
    block += "\n"
    GLOBAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not GLOBAL_LOG.exists():
        GLOBAL_LOG.write_text("# 审稿工作日志\n\n", encoding="utf-8")
    with GLOBAL_LOG.open("a", encoding="utf-8") as handle:
        handle.write(block)
    if run_dir is not None:
        local = run_dir / "worklog.md"
        if not local.exists():
            local.write_text("# Run 工作日志\n\n", encoding="utf-8")
        with local.open("a", encoding="utf-8") as handle:
            handle.write(block)
