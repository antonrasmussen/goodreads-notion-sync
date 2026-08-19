from datetime import date

from grnotion.goodreads.normalize import (
    author_last_name,
    clean_isbn,
    normalize_title,
    parse_flexible_date,
)


def test_normalize_title_strips_subtitle_and_articles():
    assert normalize_title("The DevOps Handbook: How to Create...") == "devops handbook"
    assert normalize_title("Ready to Run: Unlocking Your Potential") == "ready to run"
    assert normalize_title("The Goal (Graphic Novel)") == "goal"


def test_author_last_name_handles_formats():
    assert author_last_name("Robin Moore") == "moore"
    assert author_last_name("Moore, Robin") == "moore"
    assert author_last_name("Gene Kim; Jez Humble") == "kim"
    assert author_last_name("Clayton M. Christensen") == "christensen"


def test_clean_isbn():
    assert clean_isbn('="""9781234567890"""') == "9781234567890"
    assert clean_isbn("") == ""


def test_parse_dates():
    assert parse_flexible_date("Wed, 12 Aug 2026 10:17:53 -0700") == date(2026, 8, 12)
    assert parse_flexible_date("2026/01/15") == date(2026, 1, 15)
    assert parse_flexible_date("2012/06/01") == date(2012, 6, 1)
    assert parse_flexible_date("") is None
    assert parse_flexible_date(None) is None
