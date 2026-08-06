from pathlib import Path

from backend.core.database import Database

EXPECTED_TABLES = {
    "clients",
    "brand_profiles",
    "projects",
    "research_sessions",
    "knowledge_items",
    "content",
    "exports",
    "settings",
}


def test_init_db_creates_all_core_tables(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    db.init_db()

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    table_names = {row["name"] for row in rows}

    assert EXPECTED_TABLES.issubset(table_names)


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    db.init_db()
    db.init_db()  # should not raise


def test_foreign_keys_enforced(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    db.init_db()

    with db.connect() as conn:
        result = conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1
