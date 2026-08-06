"""SettingsService: manage application configuration (theme, default AI model,
export preferences, etc).

Unlike the other services, this one ships with a working implementation
(:class:`SQLiteSettingsService`) as part of the foundation, since other
services and the future UI need a place to read/write preferences from day
one. It is backed by the ``settings`` table (see
:mod:`backend.core.database`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.database import Database
from backend.models._shared import utcnow
from backend.models.setting import AppSetting
from backend.services.base import BaseService


class SettingsService(BaseService, ABC):
    """Defines the contract for reading and writing application settings."""

    @abstractmethod
    def get(self, key: str, default: str | None = None) -> str | None:
        """Return a setting's value, or ``default`` if it is not set."""

    @abstractmethod
    def set(self, key: str, value: str) -> AppSetting:
        """Create or update a setting."""

    @abstractmethod
    def all(self) -> dict[str, str]:
        """Return all settings as a plain key/value mapping."""


class SQLiteSettingsService(SettingsService):
    """Settings persisted as key/value rows in the app database."""

    def __init__(self, database: Database) -> None:
        super().__init__()
        self._db = database

    def get(self, key: str, default: str | None = None) -> str | None:
        with self._db.connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row is not None else default

    def set(self, key: str, value: str) -> AppSetting:
        setting = AppSetting(key=key, value=value, updated_at=utcnow())
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES (:key, :value, :updated_at)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                {
                    "key": setting.key,
                    "value": setting.value,
                    "updated_at": setting.updated_at.isoformat(),
                },
            )
        self.logger.info("Setting updated: %s", key)
        return setting

    def all(self) -> dict[str, str]:
        with self._db.connect() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: row["value"] for row in rows}
