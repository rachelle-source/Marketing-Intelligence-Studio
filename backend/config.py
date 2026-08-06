"""Application configuration, loaded from environment variables and .env.

Per the Engineering Pack security rules: secrets (e.g. the Claude API key,
Reddit API credentials) live only in environment variables / .env, never in
source, never in the database, and are never written to logs.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _detect_base_dir() -> Path:
    """Directory to treat as the app's home for default data/log/output/client
    paths, and for finding a `.env` file.

    Running from source, that's simply the repo root. Running as a
    PyInstaller-frozen build, ``__file__``-relative paths would resolve
    inside a temporary bundle-extraction directory (onefile) or a read-only
    bundle resources folder (onedir/.app) — neither is a safe place for a
    SQLite database, logs, or exported reports to live, and neither is
    somewhere a non-technical user would ever find their `.env` file. Frozen
    builds instead use the directory containing the executable (Windows), or
    the directory containing the `.app` bundle itself (macOS) — the folder
    the user actually sees next to the app they double-clicked.
    """
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        parents = exe.parents
        if len(parents) >= 2 and parents[1].name == "Contents":
            # .../Some.app/Contents/MacOS/binary -> the folder containing Some.app
            return parents[2].parent
        return exe.parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _detect_base_dir()

# Populate the real process environment from .env (if present) before
# AppConfig or anything else (e.g. backend.reddit.client.RedditClient, which
# reads REDDIT_CLIENT_ID/SECRET directly via os.environ) reads it. Existing
# real environment variables are never overridden.
load_dotenv(PROJECT_ROOT / ".env", override=False)


class AppConfig(BaseSettings):
    """Runtime configuration for the Marketing Intelligence Studio backend."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
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
