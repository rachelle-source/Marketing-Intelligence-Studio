"""Discover clients from the /clients directory.

Reads each `clients/<slug>/profile.json` written by the client intelligence
structure — see `clients/README.md`. Pure filesystem + JSON reads, no Tk
dependency, so this is fully unit-testable on its own.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClientSummary:
    """A client as shown in the client list."""

    slug: str
    display_name: str
    status: str


def _display_name(slug: str, profile: dict) -> str:
    return profile.get("client_name") or profile.get("company") or slug


def discover_clients(clients_dir: Path) -> list[ClientSummary]:
    """Return one :class:`ClientSummary` per subdirectory of ``clients_dir``
    that has a ``profile.json``. Directories without one (e.g. stray files,
    a bare README) are skipped rather than erroring.
    """
    if not clients_dir.is_dir():
        logger.warning("Clients directory does not exist: %s", clients_dir)
        return []

    summaries: list[ClientSummary] = []
    for entry in sorted(clients_dir.iterdir()):
        if not entry.is_dir():
            continue
        profile_path = entry / "profile.json"
        if not profile_path.is_file():
            continue
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Skipping client with invalid profile.json: %s", entry.name)
            continue
        summaries.append(
            ClientSummary(
                slug=entry.name,
                display_name=_display_name(entry.name, profile),
                status=profile.get("status", "unknown"),
            )
        )

    summaries.sort(key=lambda c: c.display_name.lower())
    logger.info("Discovered %d client(s) in %s", len(summaries), clients_dir)
    return summaries
