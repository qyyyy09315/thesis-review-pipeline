"""Create a review run workspace."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "agents"


def relpath(path: Path, start: Path | None = None) -> str:
    """Store portable relative paths in artifacts; never leak host absolute paths."""
    try:
        return Path(path).resolve().relative_to((start or ROOT).resolve()).as_posix()
    except ValueError:
        return Path(path).name

AGENT_FILES = {
    "stage1_linter.md": "Stage 1 预检阅读说明",
    "agent_a_motivation.md": "Agent A 动机与文献边界审查",
    "agent_b_methodology.md": "Agent B 理论推导与算法严密性审查",
    "agent_c_experiments.md": "Agent C 实证充分度与数据可信度审查",
    "consolidator.md": "Stage 3 意见聚合",
}


def new_run_id(slug: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slug}"


def create_run(
    *,
    paper_src: Path,
    ingest_md: Path,
    slug: str,
    title: str,
    field: str,
    runs_dir: Path | None = None,
) -> Path:
    runs_dir = runs_dir or (ROOT / "runs")
    run_dir = runs_dir / new_run_id(slug)
    (run_dir / "stage1").mkdir(parents=True)
    (run_dir / "agents").mkdir()
    (run_dir / "stage3").mkdir()
    shutil.copy2(ingest_md, run_dir / "paper.md")
    meta = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": relpath(paper_src),
        "ingest": relpath(ingest_md),
        "title": title,
        "field": field,
        "slug": slug,
        "stage": "stage1",
        "grade": None,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for name in AGENT_FILES:
        src = TEMPLATES / name
        dest = run_dir / "agents" / name
        if src.exists():
            shutil.copy2(src, dest)
        else:
            dest.write_text(f"# {AGENT_FILES[name]}\n\n（模板缺失，请补全）\n", encoding="utf-8")
        if name.endswith(".md") and name != "stage1_linter.md":
            json_name = name.replace(".md", ".json")
            (run_dir / "agents" / json_name).write_text(
                json.dumps(_empty_agent_payload(name), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    return run_dir


def _empty_agent_payload(name: str) -> dict:
    if name.startswith("consolidator"):
        return {
            "status": "pending",
            "grade": None,
            "contribution_summary": "",
            "grade_reason": "",
            "linter_triage": [],
            "majors": [],
            "minors": [],
            "roadmap": {
                "theory": [],
                "experiments": [],
                "writing": [],
            },
        }
    payload = {
        "status": "pending",
        "agent": name,
        "findings": [],
    }
    if "agent_c" in name:
        payload["quantitative_claims"] = True
        payload["code_status"] = "pending"
        payload["code_roots"] = []
        payload["code_note"] = ""
        payload["code_correspondence"] = []
    return payload


def load_meta(run_dir: Path) -> dict:
    return json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))


def save_meta(run_dir: Path, meta: dict) -> None:
    (run_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
