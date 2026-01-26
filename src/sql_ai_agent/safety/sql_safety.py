from __future__ import annotations

import re

_BLOCKED_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "ATTACH",
    "COPY",
    "PRAGMA",
    "EXPORT",
    "IMPORT",
)

_BLOCK_PATTERN = re.compile(r"\b(" + "|".join(_BLOCKED_KEYWORDS) + r")\b", re.IGNORECASE)


def _has_multiple_statements(sql: str) -> bool:
    stripped = sql.strip()
    if ";" not in stripped:
        return False
    parts = [part for part in stripped.split(";") if part.strip()]
    return len(parts) != 1


def is_read_only(sql: str) -> bool:
    if not sql or not sql.strip():
        return False
    if _has_multiple_statements(sql):
        return False
    if _BLOCK_PATTERN.search(sql):
        return False
    return True


def reject_unsafe_sql(sql: str) -> None:
    if not is_read_only(sql):
        raise ValueError("Unsafe SQL detected. Only single-statement read-only queries are allowed.")
