"""Delivery ledger: issue type and handling status stay separate.

New ids are R-01, R-02, ... Severity never chooses the id. Imported v1 ids
stay in legacy_id; the stored id is track plus that old id, so paper M-01
and algorithm M-01 do not collapse.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from mentions import require_mentions

ROOT = Path(__file__).resolve().parents[1]
DELIVERY_PATH = ROOT / "docs" / "delivery.local.json"
EXAMPLE_PATH = ROOT / "docs" / "delivery.example.json"

TYPES = ("defect", "claim", "evidence_gap", "accepted_limit", "improvement")
STATUSES = (
    "candidate",
    "confirmed",
    "fixed_pending_verify",
    "impl_pending_experiment",
    "evidence_ready",
    "accepted",
    "deferred",
    "superseded",
)
TRACKS = ("paper", "system", "algorithm", "overview")
SEVERITIES = ("major", "minor", "note")
NON_TERMINAL = {
    "candidate",
    "confirmed",
    "fixed_pending_verify",
    "impl_pending_experiment",
    "evidence_ready",
}
PROJECT_FIELDS = (
    "paper_version",
    "code_version",
    "data_version",
    "model_version",
    "old_experiment",
    "new_experiment",
    "deliverable_now",
    "unverified",
    "next_action",
    "decision",
    "data_split_evidence",
    "algorithm_evidence",
    "metric_evidence",
    "user_journey_evidence",
)

TYPE_LABELS = {
    "defect": "已确认缺陷",
    "claim": "待验证主张",
    "evidence_gap": "证据缺口",
    "accepted_limit": "已接受局限",
    "improvement": "交付提升建议",
}
STATUS_LABELS = {
    "candidate": "候选待证实",
    "confirmed": "已确认",
    "fixed_pending_verify": "代码已修待验证",
    "impl_pending_experiment": "实现通过待实验",
    "evidence_ready": "证据齐备",
    "accepted": "接受局限",
    "deferred": "延期",
    "superseded": "已替代",
}
TRACK_LABELS = {
    "paper": "论文",
    "system": "系统",
    "algorithm": "算法",
    "overview": "总览",
}
EVIDENCE_FIELDS = (
    ("data_split_evidence", "数据与划分"),
    ("algorithm_evidence", "核心算法"),
    ("metric_evidence", "实验数字"),
    ("user_journey_evidence", "完整用户链"),
)


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def empty_delivery() -> dict:
    return {
        "version": 2,
        "project": {key: "" for key in PROJECT_FIELDS},
        "items": [],
    }


def load_delivery(path: Path | None = None) -> dict:
    source = Path(path) if path else DELIVERY_PATH
    if not source.exists():
        return empty_delivery()
    data = json.loads(source.read_text(encoding="utf-8"))
    data.setdefault("version", 2)
    data.setdefault("items", [])
    project = data.setdefault("project", {})
    for key in PROJECT_FIELDS:
        project.setdefault(key, "")
    return data


def save_delivery(data: dict, path: Path | None = None) -> None:
    source = Path(path) if path else DELIVERY_PATH
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_review_id(data: dict) -> str:
    highest = 0
    for item in data.get("items", []):
        uid = str(item.get("id", ""))
        if not uid.startswith("R-"):
            continue
        try:
            highest = max(highest, int(uid[2:]))
        except ValueError:
            continue
    return f"R-{highest + 1:02d}"


def _check_choice(value: str, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"未知{label}：{value}（允许 {' / '.join(allowed)}）")
    return value


def add_item(
    *,
    item_type: str,
    problem: str,
    mentions: list[str],
    location: str = "",
    severity: str = "major",
    track: str = "paper",
    status: str = "candidate",
    acceptance: str = "",
    novelty: str = "new",
    path: Path | None = None,
) -> dict:
    item_type = _check_choice(item_type, TYPES, "类型")
    status = _check_choice(status, STATUSES, "状态")
    severity = _check_choice(severity, SEVERITIES, "严重性")
    track = _check_choice(track, TRACKS, "台账")
    if novelty not in {"new", "carry"}:
        raise ValueError("novelty 只能是 new 或 carry")
    if not problem.strip():
        raise ValueError("问题描述不能为空")
    cleaned = require_mentions(" ".join(mentions))
    data = load_delivery(path)
    now = _stamp()
    item = {
        "id": next_review_id(data),
        "type": item_type,
        "status": status,
        "severity": severity,
        "track": track,
        "location": location,
        "problem": problem.strip(),
        "mentions": cleaned,
        "acceptance": acceptance,
        "novelty": novelty,
        "note": "",
        "first_seen": now,
        "updated": now,
        "history": [{"at": now, "status": status, "note": "登记"}],
    }
    data["items"].append(item)
    save_delivery(data, path)
    return item


def set_status(
    item_id: str,
    status: str,
    *,
    note: str = "",
    path: Path | None = None,
) -> dict | None:
    status = _check_choice(status, STATUSES, "状态")
    data = load_delivery(path)
    for item in data["items"]:
        if item.get("id") != item_id:
            continue
        now = _stamp()
        item["status"] = status
        item["updated"] = now
        if note:
            item["note"] = note
        item.setdefault("history", []).append({"at": now, "status": status, "note": note})
        save_delivery(data, path)
        return item
    return None


def set_project(updates: dict, path: Path | None = None) -> dict:
    data = load_delivery(path)
    project = data.setdefault("project", {})
    for key in PROJECT_FIELDS:
        project.setdefault(key, "")
        if key in updates and updates[key] is not None:
            project[key] = str(updates[key])
    save_delivery(data, path)
    return project


def _import_keys(items: list[dict]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for item in items:
        track = str(item.get("track") or "")
        legacy = str(item.get("legacy_id") or "")
        if not legacy and item.get("legacy"):
            legacy = str(item.get("id") or "")
        if track and legacy:
            keys.add((track, legacy))
    return keys


def import_v1(
    v1: dict,
    *,
    mention: str,
    track: str,
    path: Path | None = None,
) -> list[dict]:
    track = _check_choice(track, TRACKS, "台账")
    mentions = require_mentions(mention)
    data = load_delivery(path)
    existing = _import_keys(data["items"])
    added: list[dict] = []
    now = _stamp()
    for issue in v1.get("issues") or []:
        uid = str(issue.get("id") or "")
        if not uid or (track, uid) in existing:
            continue
        severity = str(issue.get("severity") or "major").lower()
        if severity not in SEVERITIES:
            severity = "major"
        was_open = str(issue.get("status") or "open") == "open"
        if was_open:
            status = "confirmed"
            note = "从 v1 open 导入。v1 没有候选和已确认之分，这里记为已确认，不是新的修复。"
        else:
            status = "superseded"
            note = "从 v1 closed 导入。v1 不区分修复实测和接受局限，不得当成已经修复。"
        item_type = "defect" if severity == "major" else "improvement"
        item = {
            "id": f"{track}:{uid}",
            "legacy_id": uid,
            "type": item_type,
            "status": status,
            "severity": severity,
            "track": track,
            "location": str(issue.get("location") or ""),
            "problem": str(issue.get("problem") or ""),
            "mentions": mentions,
            "acceptance": "",
            "novelty": "carry",
            "note": note,
            "first_seen": str(issue.get("first_seen") or now),
            "updated": now,
            "history": [{"at": now, "status": status, "note": note}],
            "legacy": True,
        }
        data["items"].append(item)
        added.append(item)
        existing.add((track, uid))
    save_delivery(data, path)
    return added


def summarize(data: dict) -> dict:
    by_type: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    by_track: Counter[str] = Counter()
    for item in data.get("items") or []:
        by_type[str(item.get("type"))] += 1
        by_status[str(item.get("status"))] += 1
        by_track[str(item.get("track"))] += 1
    return {
        "by_type": dict(by_type),
        "by_status": dict(by_status),
        "by_track": dict(by_track),
    }


def _fmt_item(item: dict) -> str:
    mentions = " ".join(item.get("mentions") or []) or "（无提及）"
    novelty = "新发现" if item.get("novelty") == "new" else "沿用"
    legacy = str(item.get("legacy_id") or "")
    label = str(item.get("id") or "")
    if legacy and legacy != label:
        label = f"{label}（旧 {legacy}）"
    return (
        f"- {label} [{TRACK_LABELS.get(item.get('track'), item.get('track'))}] "
        f"{TYPE_LABELS.get(item.get('type'), item.get('type'))} / "
        f"{STATUS_LABELS.get(item.get('status'), item.get('status'))} / {novelty} "
        f"{mentions}：{item.get('problem')}"
    )


def render_overview(data: dict) -> str:
    project = data.get("project") or {}
    counts = summarize(data)
    lines = [
        "# 项目总览",
        "",
        f"本轮只回答：{project.get('decision') or '（未写）'}",
        "",
        "这一页不给全项目通过或不通过。",
        "",
        "## 版本",
        "",
        f"- 论文：{project.get('paper_version') or '（未写）'}",
        f"- 代码：{project.get('code_version') or '（未写）'}",
        f"- 数据：{project.get('data_version') or '（未写）'}",
        f"- 模型：{project.get('model_version') or '（未写）'}",
        f"- 旧实验：{project.get('old_experiment') or '（未写）'}",
        f"- 新实验：{project.get('new_experiment') or '（未写）'}",
        "",
        "## 现在可以交付",
        "",
        project.get("deliverable_now") or "（未写）",
        "",
        "## 尚未验证",
        "",
        project.get("unverified") or "（未写）",
        "",
        "## 下一项会改变决定的动作",
        "",
        project.get("next_action") or "（未写）",
        "",
        "## 首轮四条最小证据",
        "",
    ]
    missing = []
    for key, label in EVIDENCE_FIELDS:
        value = project.get(key) or ""
        if not value:
            missing.append(label)
            value = "未提供"
        lines.append(f"- {label}：{value}")
    if missing:
        lines.append("")
        lines.append("首轮四条最小证据尚未齐：" + "、".join(missing) + "。")
    lines.extend(
        [
            "",
            "## 条目",
            "",
            "类型和状态分开计。严重性不决定编号，也不代替状态。",
            "某一本专业台账全部关闭，不表示毕设可以放行。",
            "",
            "按类型："
            + (
                "、".join(f"{TYPE_LABELS.get(key, key)} {value}" for key, value in sorted(counts["by_type"].items()))
                or "（无）"
            ),
            "按状态："
            + (
                "、".join(
                    f"{STATUS_LABELS.get(key, key)} {value}" for key, value in sorted(counts["by_status"].items())
                )
                or "（无）"
            ),
            "按台账："
            + (
                "、".join(
                    f"{TRACK_LABELS.get(key, key)} {value}" for key, value in sorted(counts["by_track"].items())
                )
                or "（无）"
            ),
            "",
            "## 未结束",
            "",
        ]
    )
    open_items = [item for item in data.get("items") or [] if item.get("status") in NON_TERMINAL]
    decided = [item for item in data.get("items") or [] if item.get("status") not in NON_TERMINAL]
    if open_items:
        lines.extend(_fmt_item(item) for item in open_items)
    else:
        lines.append("（无）")
    lines.extend(["", "## 已作决定", ""])
    if decided:
        lines.extend(_fmt_item(item) for item in decided)
    else:
        lines.append("（无）")
    lines.append("")
    return "\n".join(lines)
