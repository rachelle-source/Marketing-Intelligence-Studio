"""Shared helpers for generating model identifiers and timestamps."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def new_id() -> str:
    """Generate a new opaque record identifier."""
    return uuid4().hex


def utcnow() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)
