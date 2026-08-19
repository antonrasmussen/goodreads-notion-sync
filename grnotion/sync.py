"""Orchestrate Goodreads → Notion sync."""

from __future__ import annotations

import logging
from datetime import date

from grnotion.config import Settings
from grnotion.match import match_row
from grnotion.models import Book, SyncReport
from grnotion.notion.client import (
    NotionSync,
    book_snapshot,
    book_to_library_properties,
    library_snapshot,
    reading_list_properties,
)
from grnotion.reading_list import plan_reading_list_updates

logger = logging.getLogger(__name__)


def upsert_library(
    notion: NotionSync,
    database_id: str,
    books: list[Book],
    report: SyncReport,
    *,
    dry_run: bool,
    synced: date,
) -> None:
    existing = notion.library_index(database_id)
    for book in books:
        page = existing.get(book.goodreads_id)
        properties = book_to_library_properties(book, synced)
        if page is None:
            report.library_created += 1
            report.notes.append(f"library create: {book.title} ({book.shelf})")
            if not dry_run:
                notion.create_page(database_id, properties)
            continue
        current = library_snapshot(page.get("properties") or {})
        desired = book_snapshot(book)
        if not book.cover_url:
            desired["Cover URL"] = current["Cover URL"]
            properties.pop("Cover URL", None)
        if current == desired:
            report.library_unchanged += 1
            continue
        report.library_updated += 1
        report.notes.append(f"library update: {book.title} ({book.shelf})")
        if not dry_run:
            notion.update_page(page["id"], properties)


def update_reading_list(
    notion: NotionSync,
    database_id: str,
    books: list[Book],
    report: SyncReport,
    *,
    dry_run: bool,
    reading_year: int,
    match_threshold: float,
    source: str,
) -> None:
    rows = notion.reading_list_rows(database_id)
    for row in rows:
        matched = match_row(row, books, threshold=match_threshold)
        if matched.book is None:
            report.reading_list_unchanged += 1
            label = f"{row.title} by {row.author}"
            if matched.score:
                label += f" (best score {matched.score:.0f})"
            report.unmatched.append(label)
            continue
        changes = plan_reading_list_updates(
            row,
            matched.book,
            reading_year=reading_year,
            source=source,
        )
        if not changes.has_changes():
            report.reading_list_unchanged += 1
            continue
        report.reading_list_updated += 1
        reason = "; ".join(changes.reasons) or "update"
        report.notes.append(
            f"2026 list: {row.title} [{matched.method} {matched.score:.0f}] {reason}"
        )
        if not dry_run:
            notion.update_page(row.page_id, reading_list_properties(changes))


def run_sync(
    settings: Settings,
    books: list[Book],
    *,
    dry_run: bool,
    source: str,
) -> SyncReport:
    report = SyncReport()
    if not books:
        report.notes.append("No Goodreads books found.")
        return report
    if dry_run:
        report.notes.append("Dry run — no Notion writes.")
    settings.require_notion()
    notion = NotionSync(settings.notion_token)
    upsert_library(
        notion,
        settings.notion_library_database_id,
        books,
        report,
        dry_run=dry_run,
        synced=date.today(),
    )
    update_reading_list(
        notion,
        settings.notion_reading_list_database_id,
        books,
        report,
        dry_run=dry_run,
        reading_year=settings.reading_year,
        match_threshold=settings.match_threshold,
        source=source,
    )
    return report
