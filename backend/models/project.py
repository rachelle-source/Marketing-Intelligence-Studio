"""Project models, maps to the ``projects`` table."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.models._shared import new_id, utcnow

ProjectStatus = Literal["active", "archived"]


class ProjectBase(BaseModel):
    client_id: str
    name: str
    description: str | None = None
    status: ProjectStatus = "active"


class ProjectCreate(ProjectBase):
    """Payload for creating a project."""


class ProjectUpdate(BaseModel):
    """Payload for updating a project; all fields optional."""

    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class Project(ProjectBase):
    """A stored project record."""

    id: str = Field(default_factory=new_id)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
