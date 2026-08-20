import pytest

from grnotion.config import Settings


def test_require_notion_lists_missing_values():
    settings = Settings(
        notion_token="",
        notion_library_database_id="",
        notion_reading_list_database_id="",
        goodreads_user_id="",
    )
    with pytest.raises(SystemExit, match="GOODREADS_USER_ID") as exc:
        settings.require_notion()
    message = str(exc.value)
    assert "NOTION_TOKEN" in message
    assert "GitHub Actions secrets" in message
