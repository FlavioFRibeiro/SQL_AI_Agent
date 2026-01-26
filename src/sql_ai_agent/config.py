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


def load_settings() -> Settings:
    load_dotenv()

    default_duckdb_path = str(Path("data") / "dados.duckdb")
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        duckdb_path=os.getenv("DUCKDB_PATH", default_duckdb_path),
        firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY"),
    )
