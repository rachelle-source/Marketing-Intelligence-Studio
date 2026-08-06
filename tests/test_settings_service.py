from pathlib import Path

from backend.core.database import Database
from backend.services.settings_service import SQLiteSettingsService


def make_service(tmp_path: Path) -> SQLiteSettingsService:
    db = Database(tmp_path / "test.db")
    db.init_db()
    return SQLiteSettingsService(db)


def test_get_returns_default_when_missing(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    assert service.get("theme", default="dark") == "dark"


def test_set_then_get_round_trips(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    service.set("theme", "light")
    assert service.get("theme") == "light"


def test_set_overwrites_existing_value(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    service.set("theme", "light")
    service.set("theme", "dark")
    assert service.get("theme") == "dark"


def test_all_returns_every_setting(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    service.set("theme", "dark")
    service.set("default_ai_model", "claude-sonnet-5")
    assert service.all() == {"theme": "dark", "default_ai_model": "claude-sonnet-5"}
