"""Cross-run issue ledger: machine-readable Major/Minor lifecycle.

Storage: docs/ledger.json (git-tracked; write relative paths only).
Issue ids are prefixed by severity: M-01... for major, N-01... for minor.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs" / "ledger.json"

SEVERITY_PREFIX = {"major": "M", "minor": "N"}


def load_ledger(path: Path | None = None) -> dict:
    p = Path(path) if path else LEDGER_PATH
    if not p.exists():
        return {"issues": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_ledger(data: dict, path: Path | None = None) -> None:
    p = Path(path) if path else LEDGER_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def next_id(data: dict, severity: str) -> str:
    prefix = SEVERITY_PREFIX.get(severity.lower(), "I")
    max_n = 0
    for issue in data.get("issues", []):
        uid = str(issue.get("id", ""))
        if uid.startswith(f"{prefix}-"):
            try:
                max_n = max(max_n, int(uid[len(prefix) + 1:]))
            except ValueError:
                continue
    return f"{prefix}-{max_n + 1:02d}"


def add_issue(
    *,
    severity: str,
    location: str,
    problem: str,
    run_id: str = "",
    path: Path | None = None,
) -> dict:
    data = load_ledger(path)
    issue = {
        "id": next_id(data, severity),
        "severity": severity.lower(),
        "location": location,
        "problem": problem,
        "status": "open",
        "first_seen": run_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
        "closed_in": "",
        "close_note": "",
    }
    data.setdefault("issues", []).append(issue)
    save_ledger(data, path)
    return issue


def close_issue(
    issue_id: str,
    *,
    run_id: str = "",
    note: str = "",
    path: Path | None = None,
) -> dict | None:
    data = load_ledger(path)
    for issue in data.get("issues", []):
        if issue.get("id") == issue_id and issue.get("status") == "open":
            issue["status"] = "closed"
            issue["closed_in"] = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
            issue["close_note"] = note
            save_ledger(data, path)
            return issue
    return None


def open_issues(path: Path | None = None) -> list[dict]:
    return [i for i in load_ledger(path).get("issues", []) if i.get("status") == "open"]
