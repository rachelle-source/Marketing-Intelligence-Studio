"""Generated content models, maps to the ``content`` table.

``content_type`` values mirror the AI Writer feature list in the Design Pack.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow

ContentType = Literal["blog", "linkedin_post", "reddit_reply", "email", "faq", "ad_copy"]


class ContentBase(BaseModel):
    client_id: str
    project_id: str | None = None
    content_type: ContentType
    body: str
    prompt_used: str | None = None
    model_used: str | None = None


class ContentCreate(ContentBase):
    """Payload for creating a content record."""


class Content(ContentBase):
    """A stored generated-content record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
