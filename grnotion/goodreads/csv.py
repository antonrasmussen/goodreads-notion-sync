"""Parse a Goodreads library CSV export."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from grnotion.goodreads.normalize import (
    clean_isbn,
    goodreads_book_url,
    parse_flexible_date,
)
from grnotion.models import Book


def _cell(row: dict[str, str], *names: str) -> str:
    for name in names:
        if name in row and row[name] is not None:
            return str(row[name]).strip()
    return ""


def _int(value: str) -> int | None:
    digits = "".join(ch for ch in value if ch.isdigit() or ch == "-")
    if not digits or digits == "-":
        return None
    try:
        return int(float(digits))
    except ValueError:
        return None


def _float(value: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number else None


def parse_csv_text(text: str) -> list[Book]:
    reader = csv.DictReader(StringIO(text))
    books: list[Book] = []
    for row in reader:
        goodreads_id = _int(_cell(row, "Book Id", "BookID", "book_id"))
        title = _cell(row, "Title")
        if goodreads_id is None or not title:
            continue
        additional = _cell(row, "Additional Authors")
        books.append(
            Book(
                goodreads_id=goodreads_id,
                title=title,
                author=_cell(row, "Author"),
                exclusive_shelf=_cell(row, "Exclusive Shelf"),
                additional_authors=additional,
                my_rating=_float(_cell(row, "My Rating")),
                average_rating=_float(_cell(row, "Average Rating")),
                pages=_int(_cell(row, "Number of Pages")),
                date_read=parse_flexible_date(_cell(row, "Date Read")),
                date_added=parse_flexible_date(_cell(row, "Date Added")),
                bookshelves=_cell(row, "Bookshelves"),
                isbn13=clean_isbn(_cell(row, "ISBN13", "ISBN")),
                goodreads_url=goodreads_book_url(goodreads_id),
            )
        )
    return books


def parse_csv(path: str | Path) -> list[Book]:
    return parse_csv_text(Path(path).read_text(encoding="utf-8-sig"))
