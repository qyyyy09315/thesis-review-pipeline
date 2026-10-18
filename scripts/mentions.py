"""Pull @developer and @org/team mentions out of review suggestions."""

from __future__ import annotations

import re

# @name or @org/team. A word character or dot before @ means an email, not a mention.
MENTION_RE = re.compile(
    r"(?<![\w.])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?"
    r"(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,99})?)"
)


def extract_mentions(text: str) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for match in MENTION_RE.finditer(text):
        token = "@" + match.group(1)
        if token not in found:
            found.append(token)
    return found


def require_mentions(text: str) -> list[str]:
    found = extract_mentions(text)
    if not found:
        raise ValueError(
            "建议必须 @ 至少一位开发者或一个开发者组，例如 @name 或 @org/team"
        )
    return found
