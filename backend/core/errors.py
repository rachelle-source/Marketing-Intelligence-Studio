"""Structured application errors.

Per the Design Pack rule "return structured errors instead of raw exceptions",
services should raise one of these instead of a bare Exception/ValueError so
callers (eventually the UI layer) can handle failures predictably.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all structured application errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    """Raised when a requested record does not exist."""


class ValidationError(AppError):
    """Raised when input data fails validation."""


class ServiceError(AppError):
    """Raised for unexpected failures within a service's operation."""
