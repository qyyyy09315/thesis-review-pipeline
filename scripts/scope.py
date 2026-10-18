"""Choose checks from changed paths. Unchanged areas keep their last evidence."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "docs" / "check_scope.json"


def path_matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    token = pattern.replace("\\", "/")
    if token.endswith("/**"):
        base = token[:-3].rstrip("/")
        return normalized == base or normalized.startswith(base + "/")
    return fnmatch.fnmatch(normalized, token)


def load_scope(path: Path | None = None) -> dict:
    source = Path(path) if path else SCOPE_PATH
    return json.loads(source.read_text(encoding="utf-8"))


def select_checks(changed: list[str], scope: dict) -> dict:
    areas = list(scope.get("areas") or [])
    release = list(scope.get("release_checks") or [])
    matched: list[str] = []
    run: list[str] = []
    unmatched: list[str] = []
    for raw in changed:
        hit = False
        for area in areas:
            globs = list(area.get("globs") or [])
            if any(path_matches(raw, pattern) for pattern in globs):
                hit = True
                area_id = str(area.get("id") or "")
                if area_id not in matched:
                    matched.append(area_id)
                    for check in area.get("checks") or []:
                        if check not in run:
                            run.append(check)
        if not hit:
            unmatched.append(raw.replace("\\", "/"))
    skipped = []
    for area in areas:
        area_id = str(area.get("id") or "")
        if area_id not in matched:
            skipped.append({"id": area_id, "reason": "依赖未变，沿用已有证据"})
    if unmatched:
        release_reason = "存在未登记路径，按发布点全量检查"
        release_checks = release
    elif not changed:
        release_reason = "没有给出路径变化；领域检查不重复，发布点再全量"
        release_checks = release
    else:
        release_reason = ""
        release_checks = []
    return {
        "run": run,
        "skip": skipped,
        "unmatched": unmatched,
        "release_checks": release_checks,
        "release_reason": release_reason,
    }


def render_plan(plan: dict) -> str:
    lines = ["要跑:"]
    if plan["run"]:
        lines.extend(f"- {check}" for check in plan["run"])
    else:
        lines.append("- （无）")
    lines.append("沿用（依赖未变）:")
    if plan["skip"]:
        lines.extend(f"- {item['id']}：{item['reason']}" for item in plan["skip"])
    else:
        lines.append("- （无）")
    if plan["release_reason"]:
        lines.append(plan["release_reason"] + ":")
        lines.extend(f"- {check}" for check in plan["release_checks"])
    if plan["unmatched"]:
        lines.append("未登记路径:")
        lines.extend(f"- {path}" for path in plan["unmatched"])
    return "\n".join(lines) + "\n"
