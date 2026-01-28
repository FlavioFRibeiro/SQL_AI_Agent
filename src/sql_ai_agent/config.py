from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    duckdb_path: str
    firecrawl_api_key: str | None
    saved_queries_db: str


def load_settings() -> Settings:
    load_dotenv()

    default_duckdb_path = str(Path("data") / "dados.duckdb")
    default_saved_queries_db = str(Path("data") / "saved_queries.db")
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        duckdb_path=os.getenv("DUCKDB_PATH", default_duckdb_path),
        firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
        saved_queries_db=os.getenv("SAVED_QUERIES_DB", default_saved_queries_db),
    )
