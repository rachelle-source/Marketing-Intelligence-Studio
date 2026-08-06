"""ResearchService interface: execute research workflows and collect sources.

TODO: no concrete implementation yet. Reddit research is intended to be
implemented here on top of the existing Reddit scraper, once its source is
added to :mod:`backend.reddit` (see that package's TODO).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.research import ResearchSession
from backend.services.base import BaseService


class ResearchService(BaseService, ABC):
    """Defines the contract for running research and retrieving past sessions."""

    @abstractmethod
    def run_reddit_research(self, client_id: str, query: str) -> ResearchSession:
        """Run a Reddit research pass for a client and persist the session."""

    @abstractmethod
    def list_sessions(self, client_id: str) -> list[ResearchSession]:
        """Return past research sessions for a client."""
