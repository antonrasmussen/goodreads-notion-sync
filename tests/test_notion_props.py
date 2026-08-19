from datetime import date

from grnotion.models import Book
from grnotion.notion.client import book_to_library_properties, reading_list_properties
from grnotion.models import FieldChanges
from grnotion.sync import upsert_library


class FakeNotion:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.updated: list[tuple[str, dict]] = []
        self.pages: dict[int, dict] = {}

    def library_index(self, database_id: str) -> dict[int, dict]:
        return self.pages

    def create_page(self, database_id: str, properties: dict) -> None:
        self.created.append(properties)

    def update_page(self, page_id: str, properties: dict) -> None:
        self.updated.append((page_id, properties))


def test_library_properties_include_shelf_and_id():
    book = Book(
        goodreads_id=42,
        title="Accelerate",
        author="Nicole Forsgren",
        exclusive_shelf="to-read",
        goodreads_url="https://www.goodreads.com/book/show/42",
    )
    props = book_to_library_properties(book, date(2026, 8, 18))
    assert props["Goodreads ID"]["number"] == 42
    assert props["Exclusive Shelf"]["select"]["name"] == "to-read"
    assert props["Last Synced"]["date"]["start"] == "2026-08-18"


def test_reading_list_properties_only_changed_fields():
    changes = FieldChanges(status="Reading", complete_in_goodreads=True)
    props = reading_list_properties(changes)
    assert set(props) == {"Status", "Complete in Goodreads?"}
    assert props["Status"]["status"]["name"] == "Reading"
    assert props["Complete in Goodreads?"]["checkbox"] is True


def test_upsert_library_creates_missing_and_skips_identical(monkeypatch):
    from grnotion.models import SyncReport

    book = Book(
        goodreads_id=7,
        title="Accelerate",
        author="Nicole Forsgren",
        exclusive_shelf="to-read",
        goodreads_url="https://www.goodreads.com/book/show/7",
    )
    notion = FakeNotion()
    report = SyncReport()
    upsert_library(notion, "db", [book], report, dry_run=False, synced=date(2026, 8, 18))
    assert report.library_created == 1
    assert len(notion.created) == 1
