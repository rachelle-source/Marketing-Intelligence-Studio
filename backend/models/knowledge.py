"""Knowledge item models, maps to the ``knowledge_items`` table."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow


class KnowledgeItemBase(BaseModel):
    client_id: str
    research_session_id: str | None = None
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


class KnowledgeItemCreate(KnowledgeItemBase):
    """Payload for creating a knowledge item."""


class KnowledgeItem(KnowledgeItemBase):
    """A stored knowledge item record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
