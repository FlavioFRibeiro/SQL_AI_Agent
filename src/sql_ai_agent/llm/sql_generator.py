from __future__ import annotations

import re

from openai import OpenAI

from sql_ai_agent.config import load_settings

_SYSTEM_PROMPT = (
    "You generate a single DuckDB SQL query for the user's question. "
    "Return only the SQL with no explanation, markdown, or code fences. "
    "Ensure every selected column has an explicit, meaningful alias so headers are never blank. "
    "Do not use SELECT *."
)
_EXPLAIN_PROMPT = (
    "You explain what a SQL query does in clear, concise English. "
    "Use 2-4 short sentences. Do not include markdown."
)


def _strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
    return text.strip()


def generate_sql(question: str, schema_context: str) -> str:
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Schema:\n{schema_context}\n\nQuestion:\n{question}\n\nSQL:",
            },
        ],
    )

    content = response.choices[0].message.content or ""
    return _strip_code_fences(content)


def explain_sql(sql: str, schema_context: str) -> str:
    settings = load_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": _EXPLAIN_PROMPT},
            {
                "role": "user",
                "content": f"Schema:\n{schema_context}\n\nSQL:\n{sql}\n\nExplain:",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()
