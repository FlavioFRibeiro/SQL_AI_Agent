from __future__ import annotations

from pathlib import Path

from sql_ai_agent.config import load_settings
from sql_ai_agent.db.duckdb_client import DuckDBClient
from sql_ai_agent.llm.sql_generator import explain_sql, generate_sql
from sql_ai_agent.safety.sql_safety import reject_unsafe_sql


def _get_db_client() -> DuckDBClient:
    settings = load_settings()
    db_path = settings.duckdb_path
    if db_path != ":memory:" and not Path(db_path).exists():
        raise FileNotFoundError(f"DuckDB file not found at '{db_path}'.")
    return DuckDBClient(db_path)


def _build_schema_context(db: DuckDBClient) -> str:
    tables = db.list_tables()
    if not tables:
        raise ValueError("No tables found in the DuckDB database.")

    lines = ["Tables:"]
    for table in tables:
        info = db.describe_table(table)
        columns = ", ".join(f"{row['name']} {row['type']}" for _, row in info.iterrows())
        lines.append(f"- {table}: {columns}")
    return "\n".join(lines)


def get_schema_context() -> str:
    db = _get_db_client()
    return _build_schema_context(db)


def prepare_question(question: str) -> dict:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    db = _get_db_client()
    schema_context = _build_schema_context(db)
    sql = generate_sql(question, schema_context)
    return {"sql": sql, "schema_context": schema_context, "notes": []}


def execute_sql(sql: str):
    if not sql.strip():
        raise ValueError("SQL is empty.")

    reject_unsafe_sql(sql)
    db = _get_db_client()
    return db.query(sql)


def run(question: str) -> dict:
    result = prepare_question(question)
    result["df"] = execute_sql(result["sql"])
    return result


def explain(sql: str, schema_context: str) -> str:
    return explain_sql(sql, schema_context)
