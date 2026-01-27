from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class SavedQuery:
    id: int
    name: str
    question: str
    sql: str
    created_at: str
    tag: str | None
    notes: str | None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    question TEXT NOT NULL,
    sql TEXT NOT NULL,
    created_at TEXT NOT NULL,
    tag TEXT,
    notes TEXT
);
"""


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute(_SCHEMA)


def save_query(
    db_path: str,
    name: str,
    question: str,
    sql: str,
    tag: str | None = None,
    notes: str | None = None,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as con:
        cursor = con.execute(
            """
            INSERT INTO saved_queries (name, question, sql, created_at, tag, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, question, sql, created_at, tag, notes),
        )
        con.commit()
        return int(cursor.lastrowid)


def list_queries(db_path: str, search: str | None = None) -> list[SavedQuery]:
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        if search:
            like = f"%{search}%"
            rows = con.execute(
                """
                SELECT id, name, question, sql, created_at, tag, notes
                FROM saved_queries
                WHERE name LIKE ? OR question LIKE ? OR tag LIKE ?
                ORDER BY created_at DESC
                """,
                (like, like, like),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT id, name, question, sql, created_at, tag, notes
                FROM saved_queries
                ORDER BY created_at DESC
                """
            ).fetchall()

    return [
        SavedQuery(
            id=row["id"],
            name=row["name"],
            question=row["question"],
            sql=row["sql"],
            created_at=row["created_at"],
            tag=row["tag"],
            notes=row["notes"],
        )
        for row in rows
    ]


def get_query(db_path: str, query_id: int) -> SavedQuery | None:
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            """
            SELECT id, name, question, sql, created_at, tag, notes
            FROM saved_queries
            WHERE id = ?
            """,
            (query_id,),
        ).fetchone()

    if not row:
        return None

    return SavedQuery(
        id=row["id"],
        name=row["name"],
        question=row["question"],
        sql=row["sql"],
        created_at=row["created_at"],
        tag=row["tag"],
        notes=row["notes"],
    )
