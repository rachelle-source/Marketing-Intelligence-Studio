"""Brand profile models, maps to the ``brand_profiles`` table.

Holds the voice/tone/keyword fields listed under "Client Schema" in the
Foundation Docs, keyed to a client.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow


class BrandProfileBase(BaseModel):
    client_id: str
    brand_voice: str | None = None
    tone: str | None = None
    seo_keywords: list[str] = Field(default_factory=list)
    avoid_words: list[str] = Field(default_factory=list)
    prompt_templates: list[str] = Field(default_factory=list)


class BrandProfileCreate(BrandProfileBase):
    """Payload for creating a brand profile."""


class BrandProfileUpdate(BaseModel):
    """Payload for updating a brand profile; all fields optional."""

    brand_voice: str | None = None
    tone: str | None = None
    seo_keywords: list[str] | None = None
    avoid_words: list[str] | None = None
    prompt_templates: list[str] | None = None


class BrandProfile(BrandProfileBase):
    """A stored brand profile record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
