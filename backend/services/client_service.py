"""ClientService interface: create, update, load, and delete clients.

TODO: no concrete implementation yet. Wire this up to
:class:`backend.core.database.Database` once client CRUD is implemented.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.client import Client, ClientCreate, ClientUpdate
from backend.services.base import BaseService


class ClientService(BaseService, ABC):
    """Defines the contract for managing client records."""

    @abstractmethod
    def create_client(self, data: ClientCreate) -> Client:
        """Create and persist a new client."""

    @abstractmethod
    def get_client(self, client_id: str) -> Client:
        """Load a single client by id. Raises NotFoundError if missing."""

    @abstractmethod
    def list_clients(self) -> list[Client]:
        """Return all known clients."""

    @abstractmethod
    def update_client(self, client_id: str, data: ClientUpdate) -> Client:
        """Apply a partial update to an existing client."""

    @abstractmethod
    def delete_client(self, client_id: str) -> None:
        """Delete a client and its associated records."""
