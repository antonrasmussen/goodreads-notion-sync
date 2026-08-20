"""CLI entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grnotion.config import Settings
from grnotion.goodreads.csv import parse_csv
from grnotion.goodreads.rss import fetch_shelves, merge_books
from grnotion.sync import run_sync


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )


def cmd_sync_rss(args: argparse.Namespace) -> None:
    settings = Settings()
    settings.require_notion()
    books = fetch_shelves(
        settings.goodreads_user_id,
        rss_key=settings.goodreads_rss_key,
        user_agent=settings.http_user_agent,
    )
    report = run_sync(settings, books, dry_run=args.dry_run, source="rss")
    print(report.summary())


def cmd_sync_csv(args: argparse.Namespace) -> None:
    settings = Settings()
    settings.require_notion()
    csv_books = parse_csv(args.csv_path)
    if args.with_rss:
        rss_books = fetch_shelves(
            settings.goodreads_user_id,
            rss_key=settings.goodreads_rss_key,
            user_agent=settings.http_user_agent,
        )
        books = merge_books(csv_books, rss_books)
    else:
        books = csv_books
    report = run_sync(settings, books, dry_run=args.dry_run, source="csv")
    print(report.summary())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync Goodreads shelves into Notion.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    rss = sub.add_parser("sync-rss", help="Incremental sync from Goodreads RSS (~100/shelf).")
    rss.add_argument("--dry-run", action="store_true")
    rss.set_defaults(func=cmd_sync_rss)

    csv_cmd = sub.add_parser(
        "sync-csv",
        help="Full-history sync from a Goodreads CSV export.",
    )
    csv_cmd.add_argument("csv_path", type=Path)
    csv_cmd.add_argument("--dry-run", action="store_true")
    csv_cmd.add_argument(
        "--with-rss",
        action="store_true",
        help="Overlay live RSS shelves on top of the CSV (RSS wins on overlap).",
    )
    csv_cmd.set_defaults(func=cmd_sync_csv)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
