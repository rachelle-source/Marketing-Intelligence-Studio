"""Load the bits of a client's file-based intelligence (see clients/README.md)
that the Reddit research pipeline needs: SEO keywords for query generation
and competitor names for mention detection.

Missing or scaffold-only clients (e.g. ``"status": "no_source_data"``) simply
yield empty lists rather than erroring — research can still run, just
without keyword-expanded queries or competitor detection.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClientResearchContext:
    """The subset of a client's intelligence relevant to Reddit research."""

    client_id: str
    display_name: str
    primary_keywords: list[str] = field(default_factory=list)
    competitor_names: list[str] = field(default_factory=list)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Invalid JSON, ignoring: %s", path)
        return {}


def _competitor_names(competitors: dict) -> list[str]:
    names: list[str] = []
    for entry in competitors.get("named_competitors", []):
        if isinstance(entry, dict) and entry.get("name"):
            names.append(entry["name"])
    for entry in competitors.get("competing_concepts_and_organizations", []):
        if isinstance(entry, dict) and entry.get("name"):
            names.append(entry["name"])
    for entry in competitors.get("competitors", []):
        if isinstance(entry, dict) and entry.get("name"):
            names.append(entry["name"])
        elif isinstance(entry, str):
            names.append(entry)
    return names


def load_client_context(clients_dir: Path, client_id: str) -> ClientResearchContext:
    """Load display name, SEO keywords, and competitor names for ``client_id``."""
    client_dir = clients_dir / client_id
    profile = _load_json(client_dir / "profile.json")
    seo = _load_json(client_dir / "seo.json")
    competitors = _load_json(client_dir / "competitors.json")

    display_name = profile.get("client_name") or profile.get("company") or client_id

    context = ClientResearchContext(
        client_id=client_id,
        display_name=display_name,
        primary_keywords=list(seo.get("primary_keywords", [])),
        competitor_names=_competitor_names(competitors),
    )
    logger.info(
        "Loaded research context for %s: %d keyword(s), %d competitor name(s)",
        client_id,
        len(context.primary_keywords),
        len(context.competitor_names),
    )
    return context
