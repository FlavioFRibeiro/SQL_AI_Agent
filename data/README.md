This folder stores local data files used by the app.

- `dados.duckdb` contains a small demo dataset of books from books.toscrape.com.
- `saved_queries.db` stores saved SQL queries created in the Streamlit UI.
- You can regenerate it by running `python scripts/build_duckdb_from_scrape.py` after setting `FIRECRAWL_API_KEY`.
