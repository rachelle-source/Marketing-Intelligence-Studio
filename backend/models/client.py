"""Client models.

Maps to the ``clients`` table. Brand-voice fields (voice, tone, keywords,
avoid words, prompt templates) live on :mod:`backend.models.brand_profile`
instead, matching the Foundation Docs' Core Tables list which names
``Clients`` and ``BrandProfiles`` as separate tables.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow


class ClientBase(BaseModel):
    """Fields a caller supplies when creating or updating a client."""

    company: str
    website: str | None = None
    industry: str | None = None
    products: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)


class ClientCreate(ClientBase):
    """Payload for :meth:`ClientService.create_client`."""


class ClientUpdate(BaseModel):
    """Payload for :meth:`ClientService.update_client`; all fields optional."""

    company: str | None = None
    website: str | None = None
    industry: str | None = None
    products: list[str] | None = None
    competitors: list[str] | None = None


class Client(ClientBase):
    """A stored client record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
