from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


KNOWN_SHELVES = frozenset({"currently-reading", "read", "to-read"})


@dataclass(frozen=True)
class Book:
    goodreads_id: int
    title: str
    author: str
    exclusive_shelf: str
    additional_authors: str = ""
    my_rating: float | None = None
    average_rating: float | None = None
    pages: int | None = None
    date_read: date | None = None
    date_added: date | None = None
    bookshelves: str = ""
    isbn13: str = ""
    goodreads_url: str = ""
    cover_url: str = ""

    @property
    def shelf(self) -> str:
        return self.exclusive_shelf if self.exclusive_shelf in KNOWN_SHELVES else "other"


@dataclass
class ReadingListRow:
    page_id: str
    title: str
    author: str
    status: str
    complete_in_goodreads: bool
    goodreads_id: int | None = None
    goodreads_url: str | None = None


@dataclass
class FieldChanges:
    goodreads_id: int | None = None
    goodreads_url: str | None = None
    complete_in_goodreads: bool | None = None
    status: str | None = None
    reasons: list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any(
            value is not None
            for value in (
                self.goodreads_id,
                self.goodreads_url,
                self.complete_in_goodreads,
                self.status,
            )
        )


@dataclass
class MatchResult:
    book: Book | None
    score: float
    method: str


@dataclass
class SyncReport:
    library_created: int = 0
    library_updated: int = 0
    library_unchanged: int = 0
    reading_list_updated: int = 0
    reading_list_unchanged: int = 0
    unmatched: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        unmatched = len(self.unmatched)
        lines = [
            f"Library: created={self.library_created} updated={self.library_updated} "
            f"unchanged={self.library_unchanged}",
            f"Reading list: updated={self.reading_list_updated} "
            f"unchanged={self.reading_list_unchanged} unmatched={unmatched}",
        ]
        if self.notes:
            lines.append("Changes:")
            lines.extend(f"  - {note}" for note in self.notes)
        if self.unmatched:
            lines.append("Unmatched 2026 books:")
            lines.extend(f"  - {title}" for title in self.unmatched)
        return "\n".join(lines)
