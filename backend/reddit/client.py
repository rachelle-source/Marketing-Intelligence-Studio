"""Thin, mockable wrapper around PRAW for read-only Reddit search.

Credentials are read from environment variables (never hardcoded, never
logged) per the Engineering Pack's security rules:

- ``REDDIT_CLIENT_ID``
- ``REDDIT_CLIENT_SECRET``
- ``REDDIT_USER_AGENT`` (optional — defaults to a generic user agent)

For unit tests, construct :class:`RedditClient` with the ``reddit=`` kwarg
pointing at a fake/mock object shaped like ``praw.Reddit`` — this bypasses
credential loading entirely and never touches the network. See
``tests/test_reddit_client.py``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

import praw
from praw.exceptions import PRAWException
from prawcore.exceptions import PrawcoreException

from backend.reddit.errors import RedditCredentialsError, RedditSearchError
from backend.reddit.models import RedditComment, RedditPost

logger = logging.getLogger(__name__)

DEFAULT_SUBREDDIT = "all"
DEFAULT_POST_LIMIT = 25
DEFAULT_COMMENT_LIMIT = 10
DEFAULT_USER_AGENT = "marketing-intelligence-studio/0.1"


class RedditClient:
    """Read-only Reddit search, normalized to :mod:`backend.reddit.models`."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
        reddit: Any | None = None,
    ) -> None:
        self._client_id = client_id or os.environ.get("REDDIT_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
        self._user_agent = user_agent or os.environ.get("REDDIT_USER_AGENT", DEFAULT_USER_AGENT)
        self._reddit = reddit

    def _get_reddit(self) -> Any:
        if self._reddit is None:
            if not self._client_id or not self._client_secret:
                raise RedditCredentialsError(
                    "Missing Reddit API credentials",
                    details={"required_env_vars": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]},
                )
            reddit = praw.Reddit(
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_agent=self._user_agent,
            )
            reddit.read_only = True
            self._reddit = reddit
        return self._reddit

    def search_posts(
        self,
        query: str,
        subreddits: Sequence[str] | None = None,
        post_limit: int = DEFAULT_POST_LIMIT,
        comment_limit: int = DEFAULT_COMMENT_LIMIT,
    ) -> list[RedditPost]:
        """Search one or more subreddits by keyword and return normalized posts."""
        reddit = self._get_reddit()
        names = list(subreddits) if subreddits else [DEFAULT_SUBREDDIT]
        posts: list[RedditPost] = []

        for name in names:
            try:
                subreddit = reddit.subreddit(name)
                for submission in subreddit.search(query, limit=post_limit):
                    posts.append(self._normalize_post(submission, comment_limit))
            except PRAWException as exc:
                logger.error("PRAW error searching r/%s for %r: %s", name, query, exc)
                raise RedditSearchError(
                    f"Failed to search r/{name}", details={"subreddit": name, "query": query}
                ) from exc
            except PrawcoreException as exc:
                logger.error("Reddit API/network error searching r/%s for %r: %s", name, query, exc)
                raise RedditSearchError(
                    f"Reddit API error while searching r/{name}",
                    details={"subreddit": name, "query": query},
                ) from exc

        logger.info(
            "Fetched %d post(s) for query=%r across %d subreddit(s)", len(posts), query, len(names)
        )
        return posts

    def _normalize_post(self, submission: Any, comment_limit: int) -> RedditPost:
        top_comments: list[RedditComment] = []
        try:
            submission.comments.replace_more(limit=0)
            for comment in list(submission.comments)[:comment_limit]:
                top_comments.append(
                    RedditComment(
                        id=comment.id,
                        author=str(comment.author) if comment.author else None,
                        body=comment.body,
                        score=comment.score,
                        created_utc=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
                    )
                )
        except (PRAWException, PrawcoreException) as exc:
            logger.warning("Could not load comments for post %s: %s", submission.id, exc)

        return RedditPost(
            id=submission.id,
            subreddit=str(submission.subreddit),
            title=submission.title,
            selftext=submission.selftext or "",
            url=submission.url,
            permalink=f"https://reddit.com{submission.permalink}",
            author=str(submission.author) if submission.author else None,
            score=submission.score,
            num_comments=submission.num_comments,
            created_utc=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            top_comments=top_comments,
        )
