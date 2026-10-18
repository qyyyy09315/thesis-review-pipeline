"""Pull-request title and body checks for this repository.

Run `python scripts/pr_check.py` in CI. It reads PR_TITLE and PR_BODY and
does not import the review CLI, so the job does not need the doc extras.
"""

from __future__ import annotations

import os
import re

from mentions import extract_mentions

TITLE_RE = re.compile(
    r"^(feat|fix|docs|test|refactor|chore|ci|perf|build)"
    r"(\([a-z0-9_./-]+\))?: \S.+"
)

# (error label, accepted heading names)
SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("摘要", ("摘要", "summary")),
    ("动机", ("动机", "motivation")),
    ("改动", ("改动", "changes")),
    ("测试", ("测试", "test plan")),
    ("决定", ("决定", "decision")),
    ("隐私", ("隐私", "privacy")),
)

# The PR must say one of these. Do not mention the latter two in the template
# instructions, or an untouched template would satisfy every option at once.
PRIVACY_ATTESTATIONS: tuple[str, ...] = ("不含个人稿件", "已脱敏", "已获授权")


def _heading(line: str) -> str:
    text = line.strip()
    if text.startswith("#"):
        text = text.lstrip("#").strip()
    return text.strip("*").strip()


def _has_section(body: str, names: tuple[str, ...]) -> bool:
    for line in body.splitlines():
        head = _heading(line).lower()
        if not head:
            continue
        for name in names:
            token = name.lower()
            if head == token:
                return True
            if head.startswith(token + " ") or head.startswith(token + ":") or head.startswith(token + "："):
                return True
            if head.startswith(token + "(") or head.startswith(token + "（"):
                return True
            if len(token) >= 2 and not token.isascii() and head.startswith(token):
                return True
    return False


def check_pull_request(title: str, body: str) -> list[str]:
    errors: list[str] = []
    if not TITLE_RE.fullmatch((title or "").strip()):
        errors.append(
            "标题要用约定式提交：type(scope): 说明，type 取 "
            "feat|fix|docs|test|refactor|chore|ci|perf|build"
        )
    text = body or ""
    if not text.strip():
        errors.append("PR 正文为空")
        return errors
    for label, names in SECTIONS:
        if not _has_section(text, names):
            errors.append(f"缺少章节：{label}（{' / '.join(names)}）")
    if not extract_mentions(text):
        errors.append("建议必须 @ 至少一位开发者（@name）或一个开发者组（@org/team）")
    if not any(token in text for token in PRIVACY_ATTESTATIONS):
        errors.append(
            "隐私一节要写明「不含个人稿件」，或「已脱敏」，或「已获授权」。"
            "个人稿件和具体审稿记录不能上传，除非已经脱敏或得到授权。"
        )
    return errors


def main() -> int:
    errors = check_pull_request(os.environ.get("PR_TITLE", ""), os.environ.get("PR_BODY", ""))
    if errors:
        print("\n".join(errors))
        return 1
    print("pr-check：通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
