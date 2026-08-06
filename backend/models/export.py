"""Export record models, maps to the ``exports`` table."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow

ExportFormat = Literal["markdown", "docx", "html", "pdf"]


class ExportRecordBase(BaseModel):
    content_id: str
    client_id: str
    format: ExportFormat
    file_path: str


class ExportRecordCreate(ExportRecordBase):
    """Payload for creating an export record."""


class ExportRecord(ExportRecordBase):
    """A stored export record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
