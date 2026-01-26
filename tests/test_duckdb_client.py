import duckdb

from sql_ai_agent.db.duckdb_client import DuckDBClient


def test_query_returns_dataframe(tmp_path):
    db_path = tmp_path / "sample.duckdb"
    with duckdb.connect(str(db_path)) as con:
        con.execute("CREATE TABLE items (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO items VALUES (1, 'alpha')")

    client = DuckDBClient(str(db_path))
    df = client.query("SELECT * FROM items ORDER BY id")
    assert df.shape == (1, 2)
    assert set(client.list_tables()) == {"items"}
    description = client.describe_table("items")
    assert "name" in description["name"].tolist()
