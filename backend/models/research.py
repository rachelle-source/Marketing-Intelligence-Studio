"""Research session models, maps to the ``research_sessions`` table.

``source_type`` identifies which research channel produced the session, e.g.
``"reddit"`` for the (pending) Reddit research integration — see
:mod:`backend.reddit`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow


class ResearchSessionBase(BaseModel):
    client_id: str
    project_id: str | None = None
    source_type: str
    query: str
    summary: str | None = None


class ResearchSessionCreate(ResearchSessionBase):
    """Payload for creating a research session."""


class ResearchSession(ResearchSessionBase):
    """A stored research session record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
