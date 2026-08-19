"""Notion API helpers."""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any

from notion_client import Client

from grnotion.models import Book, FieldChanges, ReadingListRow

WRITE_PAUSE_SECONDS = 0.35


def _plain(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    kind = prop.get("type")
    if kind == "title":
        return "".join(part.get("plain_text", "") for part in prop.get("title", []))
    if kind == "rich_text":
        return "".join(part.get("plain_text", "") for part in prop.get("rich_text", []))
    if kind == "url":
        return prop.get("url") or ""
    if kind == "select":
        selected = prop.get("select") or {}
        return selected.get("name") or ""
    if kind == "status":
        status = prop.get("status") or {}
        return status.get("name") or ""
    return ""


def _number(prop: dict[str, Any] | None) -> float | None:
    if not prop:
        return None
    return prop.get("number")


def _checkbox(prop: dict[str, Any] | None) -> bool:
    if not prop:
        return False
    return bool(prop.get("checkbox"))


def _date(prop: dict[str, Any] | None) -> date | None:
    if not prop:
        return None
    value = (prop.get("date") or {}).get("start")
    if not value:
        return None
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return date.fromisoformat(value[:10])


def _title(text: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": text[:2000]}}]}


def _rich(text: str) -> dict[str, Any]:
    return {"rich_text": [{"type": "text", "text": {"content": (text or "")[:2000]}}]}


def _num(value: float | int | None) -> dict[str, Any]:
    return {"number": value}


def _url(value: str | None) -> dict[str, Any]:
    return {"url": value or None}


def _select(name: str) -> dict[str, Any]:
    return {"select": {"name": name}}


def _status(name: str) -> dict[str, Any]:
    return {"status": {"name": name}}


def _date_prop(value: date | None) -> dict[str, Any]:
    if value is None:
        return {"date": None}
    return {"date": {"start": value.isoformat()}}


def _checkbox_prop(value: bool) -> dict[str, Any]:
    return {"checkbox": value}


def book_to_library_properties(book: Book, synced: date) -> dict[str, Any]:
    return {
        "Book": _title(book.title),
        "Author": _rich(book.author),
        "Additional Authors": _rich(book.additional_authors),
        "Goodreads ID": _num(book.goodreads_id),
        "Goodreads URL": _url(book.goodreads_url),
        "Cover URL": _url(book.cover_url),
        "Exclusive Shelf": _select(book.shelf),
        "My Rating": _num(book.my_rating),
        "Average Rating": _num(book.average_rating),
        "Pages": _num(book.pages),
        "Date Read": _date_prop(book.date_read),
        "Date Added": _date_prop(book.date_added),
        "Bookshelves": _rich(book.bookshelves),
        "ISBN13": _rich(book.isbn13),
        "Last Synced": _date_prop(synced),
    }


def library_snapshot(properties: dict[str, Any]) -> dict[str, Any]:
    """Comparable fields, excluding Last Synced."""
    rating = _number(properties.get("My Rating"))
    avg = _number(properties.get("Average Rating"))
    pages = _number(properties.get("Pages"))
    gr_id = _number(properties.get("Goodreads ID"))
    return {
        "Book": _plain(properties.get("Book")),
        "Author": _plain(properties.get("Author")),
        "Additional Authors": _plain(properties.get("Additional Authors")),
        "Goodreads ID": int(gr_id) if gr_id is not None else None,
        "Goodreads URL": _plain(properties.get("Goodreads URL")),
        "Cover URL": _plain(properties.get("Cover URL")),
        "Exclusive Shelf": _plain(properties.get("Exclusive Shelf")),
        "My Rating": rating,
        "Average Rating": avg,
        "Pages": int(pages) if pages is not None else None,
        "Date Read": _date(properties.get("Date Read")),
        "Date Added": _date(properties.get("Date Added")),
        "Bookshelves": _plain(properties.get("Bookshelves")),
        "ISBN13": _plain(properties.get("ISBN13")),
    }


def book_snapshot(book: Book) -> dict[str, Any]:
    return {
        "Book": book.title,
        "Author": book.author,
        "Additional Authors": book.additional_authors,
        "Goodreads ID": book.goodreads_id,
        "Goodreads URL": book.goodreads_url,
        "Cover URL": book.cover_url,
        "Exclusive Shelf": book.shelf,
        "My Rating": book.my_rating,
        "Average Rating": book.average_rating,
        "Pages": book.pages,
        "Date Read": book.date_read,
        "Date Added": book.date_added,
        "Bookshelves": book.bookshelves,
        "ISBN13": book.isbn13,
    }


def parse_reading_list_row(page: dict[str, Any]) -> ReadingListRow:
    props = page.get("properties") or {}
    gr_id = _number(props.get("Goodreads ID"))
    return ReadingListRow(
        page_id=page["id"],
        title=_plain(props.get("Book")),
        author=_plain(props.get("Author")),
        status=_plain(props.get("Status")) or "Not Started",
        complete_in_goodreads=_checkbox(props.get("Complete in Goodreads?")),
        goodreads_id=int(gr_id) if gr_id is not None else None,
        goodreads_url=_plain(props.get("Goodreads URL")) or None,
    )


def reading_list_properties(changes: FieldChanges) -> dict[str, Any]:
    props: dict[str, Any] = {}
    if changes.goodreads_id is not None:
        props["Goodreads ID"] = _num(changes.goodreads_id)
    if changes.goodreads_url is not None:
        props["Goodreads URL"] = _url(changes.goodreads_url)
    if changes.complete_in_goodreads is not None:
        props["Complete in Goodreads?"] = _checkbox_prop(changes.complete_in_goodreads)
    if changes.status is not None:
        props["Status"] = _status(changes.status)
    return props


class NotionSync:
    def __init__(self, token: str) -> None:
        self.client = Client(auth=token)
        self._data_sources: dict[str, str] = {}

    def data_source_id(self, database_id: str) -> str:
        if database_id not in self._data_sources:
            database = self.client.databases.retrieve(database_id=database_id)
            sources = database.get("data_sources") or []
            if not sources:
                raise RuntimeError(f"No data source found for database {database_id}")
            self._data_sources[database_id] = sources[0]["id"]
        return self._data_sources[database_id]

    def query_all(self, database_id: str) -> list[dict[str, Any]]:
        data_source_id = self.data_source_id(database_id)
        pages: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            payload: dict[str, Any] = {"data_source_id": data_source_id, "page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            response = self.client.data_sources.query(**payload)
            pages.extend(response.get("results") or [])
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        return pages

    def create_page(self, database_id: str, properties: dict[str, Any]) -> None:
        parent = {"data_source_id": self.data_source_id(database_id)}
        self.client.pages.create(parent=parent, properties=properties)
        time.sleep(WRITE_PAUSE_SECONDS)

    def update_page(self, page_id: str, properties: dict[str, Any]) -> None:
        self.client.pages.update(page_id=page_id, properties=properties)
        time.sleep(WRITE_PAUSE_SECONDS)

    def library_index(self, database_id: str) -> dict[int, dict[str, Any]]:
        index: dict[int, dict[str, Any]] = {}
        for page in self.query_all(database_id):
            gr_id = _number((page.get("properties") or {}).get("Goodreads ID"))
            if gr_id is None:
                continue
            index[int(gr_id)] = page
        return index

    def reading_list_rows(self, database_id: str) -> list[ReadingListRow]:
        return [parse_reading_list_row(page) for page in self.query_all(database_id)]
