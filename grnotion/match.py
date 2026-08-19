"""Match 2026 reading-list rows to Goodreads books."""

from __future__ import annotations

from rapidfuzz import fuzz

from grnotion.goodreads.normalize import author_last_name, normalize_title
from grnotion.models import Book, MatchResult, ReadingListRow

AUTHOR_THRESHOLD = 80
_EDITION_HINTS = ("graphic novel", "workbook", "abridged")
_SHELF_RANK = {
    "read": 0,
    "currently-reading": 1,
    "to-read": 2,
    "other": 3,
}


def edition_hint(title: str) -> str:
    lower = (title or "").lower()
    for hint in _EDITION_HINTS:
        if hint in lower:
            return hint
    return ""


def title_score(left: str, right: str) -> float:
    a = normalize_title(left)
    b = normalize_title(right)
    if not a or not b:
        return 0.0
    # token_set_ratio treats "goal" as a perfect match for "beyond the goal".
    score = min(
        float(fuzz.token_set_ratio(a, b)),
        float(fuzz.token_sort_ratio(a, b)),
    )
    left_ed = edition_hint(left)
    right_ed = edition_hint(right)
    if left_ed != right_ed:
        score -= 25
    return score


def author_score(left: str, right: str) -> float:
    a = author_last_name(left)
    b = author_last_name(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 100.0
    return float(fuzz.ratio(a, b))


def score_pair(row: ReadingListRow, book: Book) -> float:
    titles = title_score(row.title, book.title)
    authors = author_score(row.author, book.author)
    if authors < AUTHOR_THRESHOLD:
        return 0.0
    return titles


def match_row(
    row: ReadingListRow,
    books: list[Book],
    *,
    threshold: float = 90.0,
) -> MatchResult:
    by_id = {book.goodreads_id: book for book in books}
    if row.goodreads_id and row.goodreads_id in by_id:
        return MatchResult(book=by_id[row.goodreads_id], score=100.0, method="id")

    best: Book | None = None
    best_score = 0.0
    for book in books:
        score = score_pair(row, book)
        if best is None or score > best_score:
            best = book
            best_score = score
            continue
        if score == best_score and _SHELF_RANK.get(book.shelf, 9) < _SHELF_RANK.get(
            best.shelf, 9
        ):
            best = book
    if best is not None and best_score >= threshold:
        return MatchResult(book=best, score=best_score, method="fuzzy")
    return MatchResult(book=None, score=best_score, method="none")
