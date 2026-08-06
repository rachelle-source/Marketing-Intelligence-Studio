"""SQLite connection management and schema initialization.

Table layout follows the Foundation Docs' Core Tables list (Clients,
BrandProfiles, Projects, ResearchSessions, KnowledgeItems, Content, Exports,
Settings). Every table except ``settings`` (a global app-preferences store)
belongs to a client, per "every record belongs to a client".

This module only owns the schema and connections; it deliberately does not
contain per-table CRUD logic — that belongs to the individual services once
implemented, per "business logic lives in services".
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    website TEXT,
    industry TEXT,
    products TEXT NOT NULL DEFAULT '[]',
    competitors TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS brand_profiles (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(id),
    brand_voice TEXT,
    tone TEXT,
    seo_keywords TEXT NOT NULL DEFAULT '[]',
    avoid_words TEXT NOT NULL DEFAULT '[]',
    prompt_templates TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(id),
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_sessions (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(id),
    project_id TEXT REFERENCES projects(id),
    source_type TEXT NOT NULL,
    query TEXT NOT NULL,
    summary TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(id),
    research_session_id TEXT REFERENCES research_sessions(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(id),
    project_id TEXT REFERENCES projects(id),
    content_type TEXT NOT NULL,
    body TEXT NOT NULL,
    prompt_used TEXT,
    model_used TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exports (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content(id),
    client_id TEXT NOT NULL REFERENCES clients(id),
    format TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class Database:
    """Owns the SQLite connection lifecycle for a single database file."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def init_db(self) -> None:
        """Create the schema if it does not already exist. Safe to call repeatedly."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
        logger.info("Database initialized at %s", self.db_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection with foreign keys enabled, committing on success."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
