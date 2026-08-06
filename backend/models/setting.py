"""App setting model, maps to the ``settings`` table.

Unlike the other tables, settings are global application preferences (theme,
default AI model, export preferences) rather than per-client data, so there
is no ``client_id`` here.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models._shared import utcnow


class AppSetting(BaseModel):
    """A single key/value application setting."""

    key: str
    value: str
    updated_at: datetime = Field(default_factory=utcnow)
