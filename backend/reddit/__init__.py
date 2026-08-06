"""Reddit research: search, dedup/spam-filter, extract, and report.

Version 1, built on PRAW (https://praw.readthedocs.io/) rather than waiting
on the legacy scraper (``scrape.py``) referenced earlier in the project's
history, which was never actually provided — see :class:`RedditService`.

Modules:

- ``client.py`` — thin, mockable wrapper around PRAW (search + normalize)
- ``query_builder.py`` — expands a topic into keyword-aware search queries
- ``analysis.py`` — dedup, spam filter, relevance scoring, extraction
- ``client_context.py`` — loads a client's SEO keywords/competitors from
  ``clients/<slug>/`` for the two modules above
- ``service.py`` — ``RedditService``, the ``ResearchService`` implementation
- ``models.py`` — the normalized data model everything above shares
- ``errors.py`` — structured errors (credentials, search failures)

Requires ``REDDIT_CLIENT_ID`` and ``REDDIT_CLIENT_SECRET`` environment
variables (see ``.env.example``) — get them at
https://www.reddit.com/prefs/apps (create a "script" app).
"""

from backend.reddit.service import RedditService

__all__ = ["RedditService"]
