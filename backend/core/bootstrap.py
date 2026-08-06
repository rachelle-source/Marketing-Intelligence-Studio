"""Composition root: wires config, logging, and the database together.

A future entrypoint (CLI or desktop GUI) calls :func:`initialize_app` once at
startup to get a ready-to-use :class:`AppContext`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.config import AppConfig, get_config
from backend.core.database import Database
from backend.core.logging_config import configure_logging
from backend.services.settings_service import SQLiteSettingsService

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Bundles the wired-up foundation pieces for downstream callers."""

    config: AppConfig
    database: Database
    settings: SQLiteSettingsService


def initialize_app(config: AppConfig | None = None) -> AppContext:
    """Initialize logging and the database, and return the app context."""
    cfg = config or get_config()
    cfg.ensure_directories()
    configure_logging(cfg.logs_dir, cfg.log_level)

    logger.info("Starting Marketing Intelligence Studio backend (env=%s)", cfg.environment)

    database = Database(cfg.database_path)
    database.init_db()

    settings = SQLiteSettingsService(database)

    logger.info("Backend foundation initialized.")
    return AppContext(config=cfg, database=database, settings=settings)
