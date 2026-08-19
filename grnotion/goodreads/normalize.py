"""Title/author normalization and date/ISBN cleanup."""

from __future__ import annotations

import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime

from dateutil import parser as date_parser

_LEADING_ARTICLE = re.compile(r"^(the|a|an)\s+")
_PARENS = re.compile(r"\([^)]*\)")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")
_ISBN_NOISE = re.compile(r'[="\s]')


def normalize_title(title: str) -> str:
    text = (title or "").strip().lower()
    text = _PARENS.sub(" ", text)
    text = text.split(":")[0]
    text = _LEADING_ARTICLE.sub("", text)
    text = text.replace("&", " and ")
    text = _NON_ALNUM.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def first_author(author: str) -> str:
    text = (author or "").strip()
    for separator in (";", " & ", " and "):
        if separator in text:
            text = text.split(separator, 1)[0]
            break
    return text.strip()


def author_last_name(author: str) -> str:
    text = first_author(author)
    if "," in text:
        last = text.split(",", 1)[0]
    else:
        parts = text.split()
        last = parts[-1] if parts else ""
    last = last.lower()
    last = _NON_ALNUM.sub("", last)
    return last.strip()


def clean_isbn(value: str) -> str:
    return _ISBN_NOISE.sub("", value or "")


def parse_flexible_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = parsedate_to_datetime(text)
        return parsed.date()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed_dt: datetime = date_parser.parse(text, fuzzy=False)
        return parsed_dt.date()
    except (ValueError, OverflowError, TypeError):
        return None


def goodreads_book_url(goodreads_id: int) -> str:
    return f"https://www.goodreads.com/book/show/{goodreads_id}"
