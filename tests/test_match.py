from datetime import date

from grnotion.match import match_row, score_pair
from grnotion.models import Book, ReadingListRow
from grnotion.reading_list import plan_reading_list_updates


def _book(**kwargs) -> Book:
    defaults = dict(
        goodreads_id=1,
        title="The DevOps Handbook",
        author="Gene Kim",
        exclusive_shelf="currently-reading",
        goodreads_url="https://www.goodreads.com/book/show/1",
    )
    defaults.update(kwargs)
    return Book(**defaults)


def _row(**kwargs) -> ReadingListRow:
    defaults = dict(
        page_id="abc",
        title="The DevOps Handbook",
        author="Gene Kim; Jez Humble; Patrick Debois; John Willis",
        status="Not Started",
        complete_in_goodreads=False,
    )
    defaults.update(kwargs)
    return ReadingListRow(**defaults)


def test_fuzzy_match_ignores_extra_authors():
    row = _row()
    book = _book()
    assert score_pair(row, book) >= 90
    matched = match_row(row, [book])
    assert matched.book is book
    assert matched.method == "fuzzy"


def test_id_match_wins():
    row = _row(goodreads_id=99, title="Nope")
    book = _book(goodreads_id=99, title="Completely Different")
    matched = match_row(row, [book])
    assert matched.method == "id"
    assert matched.book is book


def test_rejects_low_title_overlap():
    row = _row(title="Native Son", author="Richard Wright")
    book = _book(title="Ready to Run", author="Kelly Starrett")
    matched = match_row(row, [book])
    assert matched.book is None


def test_currently_reading_sets_status():
    changes = plan_reading_list_updates(
        _row(),
        _book(exclusive_shelf="currently-reading"),
        reading_year=2026,
        source="rss",
    )
    assert changes.status == "Reading"
    assert changes.complete_in_goodreads is None


def test_read_this_year_marks_completed():
    changes = plan_reading_list_updates(
        _row(title="The Green Berets", author="Robin Moore"),
        _book(
            title="The Green Berets",
            author="Robin Moore",
            exclusive_shelf="read",
            date_read=date(2026, 1, 15),
        ),
        reading_year=2026,
        source="rss",
    )
    assert changes.complete_in_goodreads is True
    assert changes.status == "Completed"


def test_older_read_only_checks_goodreads_box():
    """Disrupting Healthcare: already finished on Goodreads, still on the 2026 plan."""
    changes = plan_reading_list_updates(
        _row(
            title="Disrupting Healthcare",
            author="Clayton M. Christensen",
            status="Not Started",
        ),
        _book(
            title="Disrupting Healthcare",
            author="Clayton M. Christensen",
            exclusive_shelf="read",
            date_read=date(2012, 6, 1),
        ),
        reading_year=2026,
        source="rss",
    )
    assert changes.complete_in_goodreads is True
    assert changes.status is None


def test_rss_does_not_uncheck_missing_older_reads():
    changes = plan_reading_list_updates(
        _row(complete_in_goodreads=True, status="Not Started"),
        _book(exclusive_shelf="to-read"),
        reading_year=2026,
        source="rss",
    )
    assert changes.complete_in_goodreads is None


def test_csv_can_uncheck_if_not_on_read_shelf():
    changes = plan_reading_list_updates(
        _row(complete_in_goodreads=True, status="Not Started"),
        _book(exclusive_shelf="to-read"),
        reading_year=2026,
        source="csv",
    )
    assert changes.complete_in_goodreads is False


def test_does_not_downgrade_completed_status():
    changes = plan_reading_list_updates(
        _row(status="Completed"),
        _book(exclusive_shelf="currently-reading"),
        reading_year=2026,
        source="rss",
    )
    assert changes.status is None
