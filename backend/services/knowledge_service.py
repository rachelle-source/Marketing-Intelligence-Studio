"""KnowledgeService interface: extract and store reusable insights.

TODO: no concrete implementation yet.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.knowledge import KnowledgeItem, KnowledgeItemCreate
from backend.services.base import BaseService


class KnowledgeService(BaseService, ABC):
    """Defines the contract for extracting and retrieving knowledge items."""

    @abstractmethod
    def extract_insights(self, research_session_id: str) -> list[KnowledgeItem]:
        """Extract reusable knowledge items from a research session."""

    @abstractmethod
    def save_item(self, item: KnowledgeItemCreate) -> KnowledgeItem:
        """Persist a knowledge item."""

    @abstractmethod
    def list_items(self, client_id: str) -> list[KnowledgeItem]:
        """Return stored knowledge items for a client."""
