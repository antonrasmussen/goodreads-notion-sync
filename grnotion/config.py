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
        if not self.notion_token:
            raise SystemExit(
                "NOTION_TOKEN is required. Create an internal integration, "
                "share both databases with it, and put the token in .env."
            )
