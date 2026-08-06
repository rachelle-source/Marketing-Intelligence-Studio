"""Structured errors for the Reddit research subsystem."""

from __future__ import annotations

from backend.core.errors import ServiceError


class RedditCredentialsError(ServiceError):
    """Raised when required Reddit API credentials are missing."""


class RedditSearchError(ServiceError):
    """Raised when a Reddit search or comment fetch fails."""
