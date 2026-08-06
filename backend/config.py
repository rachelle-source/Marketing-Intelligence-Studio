"""Application configuration, loaded from environment variables and .env.

Per the Engineering Pack security rules: secrets (e.g. the Claude API key)
live only in environment variables / .env, never in source, never in the
database, and are never written to logs.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AppConfig(BaseSettings):
    """Runtime configuration for the Marketing Intelligence Studio backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MIS_",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"

    claude_api_key: str | None = Field(default=None)

    clients_dir: Path = PROJECT_ROOT / "clients"
    logs_dir: Path = PROJECT_ROOT / "logs"
    output_dir: Path = PROJECT_ROOT / "output"
    data_dir: Path = PROJECT_ROOT / "data"

    database_path: Path = PROJECT_ROOT / "data" / "marketing_intelligence_studio.db"

    def ensure_directories(self) -> None:
        """Create the runtime directories this app depends on, if missing."""
        for directory in (self.clients_dir, self.logs_dir, self.output_dir, self.data_dir):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return the process-wide :class:`AppConfig` singleton."""
    return AppConfig()
