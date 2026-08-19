"""Conservative updates for the 2026 physical reading list."""

from __future__ import annotations

from grnotion.models import Book, FieldChanges, ReadingListRow


def plan_reading_list_updates(
    row: ReadingListRow,
    book: Book,
    *,
    reading_year: int,
    source: str,
) -> FieldChanges:
    """Decide which 2026-list fields to change for a matched Goodreads book.

    RSS-only runs never uncheck Complete in Goodreads? — older reads can fall
    out of the ~100-item RSS window. CSV imports may uncheck because they
    contain the full library.
    """
    changes = FieldChanges()

    if row.goodreads_id != book.goodreads_id:
        changes.goodreads_id = book.goodreads_id
        changes.reasons.append(f"link Goodreads ID {book.goodreads_id}")
    if not row.goodreads_url and book.goodreads_url:
        changes.goodreads_url = book.goodreads_url
        changes.reasons.append("set Goodreads URL")

    if book.exclusive_shelf == "read":
        if not row.complete_in_goodreads:
            changes.complete_in_goodreads = True
            changes.reasons.append("mark Complete in Goodreads")
    elif source == "csv" and row.complete_in_goodreads:
        changes.complete_in_goodreads = False
        changes.reasons.append("uncheck Complete in Goodreads (not on read shelf)")

    if row.status == "Completed":
        return changes

    if book.exclusive_shelf == "currently-reading" and row.status != "Reading":
        changes.status = "Reading"
        changes.reasons.append("Status -> Reading")
    elif (
        book.exclusive_shelf == "read"
        and book.date_read is not None
        and book.date_read.year == reading_year
        and row.status != "Completed"
    ):
        changes.status = "Completed"
        changes.reasons.append(f"Status -> Completed ({reading_year} date read)")

    return changes
