"""AIService interface: build prompts, call Claude, validate responses.

Per the Design/Engineering Packs, this is the *only* path through which the
application may talk to an AI provider — no other module may call Claude
directly.

TODO: no concrete implementation yet. Depends on the still-pending Claude
API integration and Prompt Builder (see project TODOs).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.services.base import BaseService


class AIService(BaseService, ABC):
    """Defines the contract for prompt construction, generation, and validation."""

    @abstractmethod
    def build_prompt(self, client_id: str, context: dict[str, Any]) -> str:
        """Build a prompt string from client context. TODO: Prompt Builder."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send a prompt to Claude and return the raw response. TODO: Claude API integration."""

    @abstractmethod
    def validate_response(self, response: str) -> bool:
        """Validate an AI response before it is saved or shown to the user."""
