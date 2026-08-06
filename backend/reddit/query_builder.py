"""Search query generation.

Turns a plain-language topic into a small set of higher-signal Reddit search
queries by pairing it with the client's own SEO keyword clusters — so
"pricing" for KORE becomes "pricing IoT connectivity", "pricing enterprise
IoT", etc. instead of a single generic search.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MAX_GENERATED_QUERIES = 4


def build_search_queries(
    topic: str,
    primary_keywords: list[str] | None = None,
    max_queries: int = MAX_GENERATED_QUERIES,
) -> list[str]:
    """Build a small set of search query variants for ``topic``.

    Always includes the bare topic first, then pairs the topic with the
    client's top primary keywords (deduplicated, case-insensitive), capped
    at ``max_queries``.
    """
    topic = topic.strip()
    queries: list[str] = [topic] if topic else []

    for keyword in primary_keywords or []:
        keyword = keyword.strip()
        if not keyword:
            continue
        candidate = f"{topic} {keyword}".strip()
        if candidate.lower() not in {q.lower() for q in queries}:
            queries.append(candidate)
        if len(queries) >= max_queries:
            break

    logger.info("Generated %d search query variant(s) for topic %r", len(queries), topic)
    return queries
