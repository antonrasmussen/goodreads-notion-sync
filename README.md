# Goodreads to Notion sync

CLI that copies Goodreads shelves into Notion. Goodreads has no public write API, so this is **Goodreads → Notion only**.

It updates two databases:

1. **Goodreads Library** — full mirror, upserted by Goodreads book ID
2. **2026 Reading List** — the physical books; matched in place, never inserted or deleted

## How data gets in

| Source | Command | What it covers |
| --- | --- | --- |
| RSS | `grnotion sync-rss` | Newest ~100 books on `currently-reading`, `read`, and `to-read` |
| CSV | `grnotion sync-csv export.csv` | Full library from [Goodreads Import/Export](https://www.goodreads.com/review/import) |

RSS is enough for currently-reading (you have 43). It cannot see all 1,000+ to-read books, so re-drop a CSV when the library mirror should catch up.

## 2026 list rules

These exist so already-finished books (for example *Disrupting Healthcare*) stay on the physical plan:

- Match by stored **Goodreads ID**, else fuzzy title + author
- `read` shelf → check **Complete in Goodreads?**
- RSS never unchecks that box (older reads fall out of the 100-item window)
- `currently-reading` → Status **Reading**
- `read` and date-read in `READING_YEAR` (default 2026) → Status **Completed**
- Does not change Month, Topics, Weight, Book #, Author, or title
- Does not downgrade **Completed**

## Setup

```bash
cd ~/repos/goodreads-notion-sync
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

1. Create a Notion [internal integration](https://www.notion.so/my-integrations) and copy the token into `NOTION_TOKEN`.
2. Share **Goodreads Library** and **2026 Reading List** with that integration.
3. Preview:

```bash
grnotion sync-rss --dry-run
```

4. First full backfill (optional but recommended):

```bash
# My Books → Import/Export → Export Library
grnotion sync-csv ~/Downloads/goodreads_library_export.csv --dry-run
grnotion sync-csv ~/Downloads/goodreads_library_export.csv --with-rss
```

## GitHub Action

The workflow in `.github/workflows/sync.yml` runs `sync-rss` every 6 hours.

Repo secrets:

- `NOTION_TOKEN`
- `NOTION_LIBRARY_DATABASE_ID`
- `NOTION_READING_LIST_DATABASE_ID`
- `GOODREADS_USER_ID`

Cursor/MCP access is not available to GitHub Actions. The Action needs its own integration token.

## Tests

```bash
pytest
```
