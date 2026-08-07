"""Generates reddit-tool client configs (see ``reddit-tool/README.md``) from
Marketing Intelligence Studio's own client knowledge (``clients/<slug>/*.json``).

The reddit-tool is a separate, already-working project vendored into this repo
at ``reddit-tool/`` — it is not rewritten or replaced here. Its own
``src/config.py`` still defines and validates the config schema it loads. What
this module does is stand between that tool and a human: instead of a person
hand-editing ``reddit-tool/clients/<slug>.json``, this module derives that file
from the client knowledge already stored in ``clients/<slug>/profile.json`` and
``seo.json``, so the client knowledge stays the single source of truth.

``profile.json`` carries a ``reddit_config`` section (subreddits, tone,
notify_email, max_threads, sort) for the fields that aren't marketing facts
about the client and can't be derived from anything else already in
``clients/`` — see any populated client's profile.json for the convention.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "client_name",
    "subreddits",
    "keywords",
    "brand_context",
    "notify_email",
    "max_threads",
    "sort",
]
VALID_SORTS = {"hot", "new", "top"}

DEFAULT_MAX_THREADS = 15
DEFAULT_SORT = "hot"
DEFAULT_NOTIFY_EMAIL = "marketing@keystonedigitalservices.com"


class ConfigGenerationError(Exception):
    """Raised when a client's knowledge is insufficient to generate a Reddit tool config."""


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Invalid JSON, ignoring: %s", path)
        return {}


def _build_brand_context(profile: dict, reddit_config: dict) -> str:
    company = profile.get("client_name") or profile.get("company") or ""
    description = profile.get("description") or profile.get("core_promise") or ""
    tone = reddit_config.get("tone")

    context = " ".join(part for part in (f"{company}." if company else "", description) if part).strip()
    if tone:
        context = f"{context} Tone: {tone.rstrip('.')}.".strip()
    return context


def generate_client_config(clients_dir: Path, client_id: str) -> dict:
    """Build the reddit-tool config dict for ``client_id`` from its client knowledge.

    Raises :class:`ConfigGenerationError` if the client is missing a
    ``profile.json``, a display name, SEO keywords, or a ``reddit_config``
    with subreddits — none of those can be safely defaulted or invented.
    """
    client_dir = clients_dir / client_id
    profile_path = client_dir / "profile.json"
    if not profile_path.is_file():
        raise ConfigGenerationError(f"No profile.json found for client '{client_id}' at {client_dir}")
    profile = _load_json(profile_path)
    seo = _load_json(client_dir / "seo.json")

    client_name = profile.get("client_name") or profile.get("company")
    if not client_name:
        raise ConfigGenerationError(f"'{client_id}' profile.json has no client_name or company")

    reddit_config = profile.get("reddit_config") or {}
    subreddits = list(reddit_config.get("subreddits") or [])
    if not subreddits:
        raise ConfigGenerationError(
            f"'{client_id}' profile.json has no reddit_config.subreddits — "
            "add one before generating a Reddit tool config for this client"
        )

    keywords = list(seo.get("primary_keywords") or [])
    if not keywords:
        raise ConfigGenerationError(
            f"'{client_id}' seo.json has no primary_keywords — "
            "add some before generating a Reddit tool config for this client"
        )

    sort = reddit_config.get("sort", DEFAULT_SORT)
    if sort not in VALID_SORTS:
        raise ConfigGenerationError(f"'{client_id}' reddit_config.sort must be one of {VALID_SORTS}, got '{sort}'")

    brand_context = _build_brand_context(profile, reddit_config)
    if not brand_context:
        raise ConfigGenerationError(
            f"'{client_id}' profile.json has no description/core_promise to build brand_context from"
        )

    config = {
        "client_name": client_name,
        "subreddits": subreddits,
        "keywords": keywords,
        "brand_context": brand_context,
        "notify_email": reddit_config.get("notify_email") or DEFAULT_NOTIFY_EMAIL,
        "max_threads": reddit_config.get("max_threads") or DEFAULT_MAX_THREADS,
        "sort": sort,
    }

    missing = [field for field in REQUIRED_FIELDS if not config.get(field)]
    if missing:
        raise ConfigGenerationError(f"'{client_id}' generated config is missing required field(s): {missing}")

    return config


def write_client_config(clients_dir: Path, client_id: str, reddit_tool_clients_dir: Path) -> Path:
    """Generate and write ``reddit_tool_clients_dir/<client_id>.json``."""
    config = generate_client_config(clients_dir, client_id)
    reddit_tool_clients_dir.mkdir(parents=True, exist_ok=True)
    out_path = reddit_tool_clients_dir / f"{client_id}.json"
    out_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    logger.info("Generated reddit-tool config for '%s' -> %s", client_id, out_path)
    return out_path


def generate_all(clients_dir: Path, reddit_tool_clients_dir: Path) -> dict[str, Path | ConfigGenerationError]:
    """Generate a reddit-tool config for every client under ``clients_dir``.

    Clients that can't be generated (no ``reddit_config``, no SEO keywords,
    etc.) are skipped with their error recorded rather than aborting the run
    for every other client.
    """
    results: dict[str, Path | ConfigGenerationError] = {}
    for client_dir in sorted(p for p in clients_dir.iterdir() if p.is_dir()):
        client_id = client_dir.name
        try:
            results[client_id] = write_client_config(clients_dir, client_id, reddit_tool_clients_dir)
        except ConfigGenerationError as exc:
            logger.warning("Skipping '%s': %s", client_id, exc)
            results[client_id] = exc
    return results


def _main() -> None:
    import argparse

    from backend.config import PROJECT_ROOT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("client", nargs="?", help="Client slug to generate a config for. Omit to generate all.")
    parser.add_argument("--clients-dir", type=Path, default=PROJECT_ROOT / "clients")
    parser.add_argument("--reddit-tool-clients-dir", type=Path, default=PROJECT_ROOT / "reddit-tool" / "clients")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.client:
        path = write_client_config(args.clients_dir, args.client, args.reddit_tool_clients_dir)
        print(f"Wrote {path}")
        return

    results = generate_all(args.clients_dir, args.reddit_tool_clients_dir)
    for client_id, result in results.items():
        if isinstance(result, Path):
            print(f"OK      {client_id} -> {result}")
        else:
            print(f"SKIPPED {client_id}: {result}")


if __name__ == "__main__":
    _main()
