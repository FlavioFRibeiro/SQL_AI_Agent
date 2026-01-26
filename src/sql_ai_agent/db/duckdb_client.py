from __future__ import annotations

from typing import List

import duckdb
import pandas as pd


class DuckDBClient:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def query(self, sql: str) -> pd.DataFrame:
        with duckdb.connect(database=self._db_path, read_only=True) as con:
            return con.execute(sql).df()

    def list_tables(self) -> List[str]:
        with duckdb.connect(database=self._db_path, read_only=True) as con:
            rows = con.execute("SHOW TABLES").fetchall()
        return [row[0] for row in rows]

    def describe_table(self, table: str) -> pd.DataFrame:
        with duckdb.connect(database=self._db_path, read_only=True) as con:
            return con.execute(f"PRAGMA table_info('{table}')").df()
