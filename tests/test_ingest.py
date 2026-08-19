from datetime import date
from pathlib import Path

from grnotion.goodreads.csv import parse_csv
from grnotion.goodreads.rss import merge_books, parse_rss

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_currently_reading_rss():
    xml = (FIXTURES / "currently_reading.xml").read_text()
    books = parse_rss(xml, exclusive_shelf="currently-reading")
    assert len(books) == 2
    ready = books[0]
    assert ready.goodreads_id == 18668429
    assert ready.title.startswith("Ready to Run")
    assert ready.author == "Kelly Starrett"
    assert ready.exclusive_shelf == "currently-reading"
    assert ready.pages == 288
    assert ready.date_added == date(2026, 8, 12)
    assert ready.date_read is None
    assert ready.my_rating is None
    assert ready.cover_url.endswith("ready.jpg")
    assert ready.goodreads_url == "https://www.goodreads.com/book/show/18668429"


def test_parse_read_rss_dates():
    xml = (FIXTURES / "read.xml").read_text()
    books = parse_rss(xml, exclusive_shelf="read")
    green = next(book for book in books if book.goodreads_id == 111111)
    older = next(book for book in books if book.goodreads_id == 222222)
    assert green.date_read == date(2026, 1, 15)
    assert green.my_rating == 4
    assert older.date_read == date(2012, 6, 1)


def test_parse_csv_export():
    books = parse_csv(FIXTURES / "library_export.csv")
    by_id = {book.goodreads_id: book for book in books}
    assert set(by_id) == {111111, 222222, 34557467, 999999}
    green = by_id[111111]
    assert green.title == "The Green Berets"
    assert green.isbn13 == "9781234567890"
    assert green.date_read == date(2026, 1, 15)
    assert green.exclusive_shelf == "read"
    assert by_id[34557467].exclusive_shelf == "currently-reading"
    assert by_id[34557467].date_read is None


def test_merge_prefers_later_group():
    xml = (FIXTURES / "currently_reading.xml").read_text()
    rss_books = parse_rss(xml, exclusive_shelf="currently-reading")
    csv_books = parse_csv(FIXTURES / "library_export.csv")
    merged = merge_books(csv_books, rss_books)
    devops = next(book for book in merged if book.goodreads_id == 34557467)
    assert devops.cover_url.endswith("devops.jpg")
    assert devops.exclusive_shelf == "currently-reading"
