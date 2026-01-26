from __future__ import annotations

import logging
import sys
from pathlib import Path

import duckdb
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sql_ai_agent.config import load_settings  # noqa: E402
from sql_ai_agent.utils.logging import setup_logging  # noqa: E402

URL_TO_SCRAPE = "https://books.toscrape.com/"


def scrape_html(api_key: str) -> str:
    app = FirecrawlApp(api_key=api_key)
    result = app.scrape_url(URL_TO_SCRAPE, params={"formats": ["html"]})
    html = result.get("html")
    if not html:
        raise RuntimeError("Scrape completed but no HTML was returned.")
    return html


def parse_books(html: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "lxml")
    books: list[dict[str, object]] = []

    for pod in soup.select("article.product_pod"):
        title_tag = pod.select_one("h3 a")
        title = title_tag["title"].strip() if title_tag and title_tag.has_attr("title") else None

        price_tag = pod.select_one("div.product_price p.price_color")
        price = None
        if price_tag:
            price_text = price_tag.get_text()
            price_text = price_text.replace("\u00a3", "").replace("\u00c2\u00a3", "").strip()
            try:
                price = float(price_text)
            except ValueError:
                logging.warning("Unable to parse price: %s", price_text)

        if title and price is not None:
            books.append({"title": title, "price": price})

    return books


def write_duckdb(db_path: str, books: list[dict[str, object]]) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(database=db_path, read_only=False) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                title VARCHAR,
                price DECIMAL(10, 2)
            );
            """
        )
        con.execute("DELETE FROM books;")
        con.executemany(
            "INSERT INTO books (title, price) VALUES (?, ?)",
            [(book["title"], book["price"]) for book in books],
        )


def main() -> None:
    setup_logging()
    settings = load_settings()

    if not settings.firecrawl_api_key:
        raise ValueError("FIRECRAWL_API_KEY is not set.")

    html = scrape_html(settings.firecrawl_api_key)
    books = parse_books(html)
    if not books:
        raise RuntimeError("No book records were parsed from the scraped HTML.")

    write_duckdb(settings.duckdb_path, books)
    logging.info("Wrote %d books to %s", len(books), settings.duckdb_path)


if __name__ == "__main__":
    main()
