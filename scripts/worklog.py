"""Append-only work log for the thesis review workspace."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_LOG = ROOT / "docs" / "worklog.md"


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
