"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    notion_token: str = ""
    notion_library_database_id: str = ""
    notion_reading_list_database_id: str = ""
    goodreads_user_id: str = ""
    goodreads_rss_key: str = ""
    reading_year: int = 2026
    match_threshold: float = 90.0
    http_user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def require_notion(self) -> None:
        missing = [
            name
            for name, value in (
                ("NOTION_TOKEN", self.notion_token),
                ("NOTION_LIBRARY_DATABASE_ID", self.notion_library_database_id),
                (
                    "NOTION_READING_LIST_DATABASE_ID",
                    self.notion_reading_list_database_id,
                ),
                ("GOODREADS_USER_ID", self.goodreads_user_id),
            )
            if not value
        ]
        if missing:
            raise SystemExit(
                "Missing required config: "
                + ", ".join(missing)
                + ". Set them in .env or GitHub Actions secrets."
            )
