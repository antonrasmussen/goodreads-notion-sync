"""Parse Goodreads RSS shelf feeds."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from grnotion.goodreads.normalize import (
    clean_isbn,
    goodreads_book_url,
    parse_flexible_date,
)
from grnotion.models import Book

logger = logging.getLogger(__name__)

DEFAULT_SHELVES = ("to-read", "read", "currently-reading")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def rss_url(user_id: str, shelf: str, rss_key: str = "") -> str:
    url = (
        f"https://www.goodreads.com/review/list_rss/{user_id}"
        f"?shelf={shelf}&per_page=100"
    )
    if rss_key:
        url += f"&key={rss_key}"
    return url


def _text(item: ET.Element, tag: str) -> str:
    child = item.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def _int(value: str) -> int | None:
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return None
    return int(digits)


def _float(value: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number else None


def parse_rss(xml_text: str, exclusive_shelf: str | None = None) -> list[Book]:
    root = ET.fromstring(xml_text)
    books: list[Book] = []
    for item in root.findall("./channel/item"):
        raw_id = _text(item, "book_id")
        goodreads_id = _int(raw_id)
        title = _text(item, "title")
        if goodreads_id is None or not title:
            continue
        pages_el = item.find("book/num_pages")
        pages = _int(pages_el.text if pages_el is not None and pages_el.text else "")
        shelves = _text(item, "user_shelves")
        shelf = exclusive_shelf or (shelves.split(",")[0].strip() if shelves else "")
        rating = _float(_text(item, "user_rating"))
        books.append(
            Book(
                goodreads_id=goodreads_id,
                title=title,
                author=_text(item, "author_name"),
                exclusive_shelf=shelf,
                my_rating=rating,
                average_rating=_float(_text(item, "average_rating")),
                pages=pages,
                date_read=parse_flexible_date(_text(item, "user_read_at")),
                date_added=parse_flexible_date(_text(item, "user_date_added")),
                bookshelves=shelves,
                isbn13=clean_isbn(_text(item, "isbn")),
                goodreads_url=goodreads_book_url(goodreads_id),
                cover_url=_text(item, "book_large_image_url")
                or _text(item, "book_image_url"),
            )
        )
    return books


def merge_books(*groups: list[Book]) -> list[Book]:
    """Later groups overwrite earlier ones for the same Goodreads ID."""
    by_id: dict[int, Book] = {}
    for group in groups:
        for book in group:
            by_id[book.goodreads_id] = book
    return list(by_id.values())


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _get(url: str, user_agent: str) -> str:
    headers = {"User-Agent": user_agent, "Accept": "application/rss+xml, application/xml"}
    with httpx.Client(timeout=30.0, follow_redirects=True, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def fetch_shelves(
    user_id: str,
    *,
    shelves: tuple[str, ...] = DEFAULT_SHELVES,
    rss_key: str = "",
    user_agent: str = USER_AGENT,
) -> list[Book]:
    groups: list[list[Book]] = []
    for shelf in shelves:
        url = rss_url(user_id, shelf, rss_key)
        logger.info("Fetching Goodreads RSS shelf %s", shelf)
        xml_text = _get(url, user_agent)
        books = parse_rss(xml_text, exclusive_shelf=shelf)
        logger.info("Parsed %s books from %s", len(books), shelf)
        groups.append(books)
    return merge_books(*groups)
