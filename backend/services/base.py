"""Shared base class for services."""

from __future__ import annotations

import logging


class BaseService:
    """Provides a per-service logger. Concrete services subclass this."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__module__)
