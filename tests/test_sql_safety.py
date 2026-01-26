import pytest

from sql_ai_agent.safety.sql_safety import is_read_only, reject_unsafe_sql


def test_allows_select():
    sql = "SELECT * FROM books"
    assert is_read_only(sql)
    reject_unsafe_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE books",
        "insert into books values (1, 'x')",
        "UPDATE books SET price = 10",
        "DELETE FROM books",
        "PRAGMA table_info('books')",
    ],
)
def test_blocks_write_keywords(sql):
    assert not is_read_only(sql)
    with pytest.raises(ValueError):
        reject_unsafe_sql(sql)


def test_blocks_multiple_statements():
    sql = "SELECT * FROM books; SELECT * FROM books"
    assert not is_read_only(sql)
    with pytest.raises(ValueError):
        reject_unsafe_sql(sql)


def test_allows_trailing_semicolon():
    sql = "SELECT * FROM books;"
    assert is_read_only(sql)
