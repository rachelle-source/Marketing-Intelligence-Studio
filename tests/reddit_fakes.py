"""Fake PRAW objects for unit-testing backend.reddit without network access.

Shaped just enough like `praw.Reddit`/`Submission`/Comment for
`RedditClient._normalize_post` to work against them.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class FakeComment:
    id: str
    body: str
    score: int = 1
    author: str | None = "commenter"
    created_utc: float = field(default_factory=lambda: time.time())


class FakeCommentForest(list):
    def replace_more(self, limit: int = 0) -> None:  # noqa: ARG002 - matches PRAW's signature
        return None


@dataclass
class FakeSubmission:
    id: str
    title: str
    selftext: str = ""
    url: str = "https://example.com"
    permalink: str = "/r/test/comments/abc123/example/"
    author: str | None = "poster"
    score: int = 10
    num_comments: int = 2
    created_utc: float = field(default_factory=lambda: time.time())
    comments: FakeCommentForest = field(default_factory=lambda: FakeCommentForest())
    subreddit: str = "test"


class FakeSubreddit:
    def __init__(self, name: str, submissions: list[FakeSubmission] | None = None) -> None:
        self.name = name
        self._submissions = submissions or []

    def __str__(self) -> str:
        return self.name

    def search(self, query: str, limit: int = 25):  # noqa: ARG002 - fake ignores query filtering
        return iter(self._submissions[:limit])


class FakeReddit:
    def __init__(self, subreddits: dict[str, FakeSubreddit] | None = None) -> None:
        self._subreddits = subreddits or {}
        self.read_only = False

    def subreddit(self, name: str) -> FakeSubreddit:
        if name not in self._subreddits:
            self._subreddits[name] = FakeSubreddit(name)
        return self._subreddits[name]

    def submission(self, id: str) -> FakeSubmission:  # noqa: A002 - matches PRAW's kwarg name
        for subreddit in self._subreddits.values():
            for submission in subreddit._submissions:
                if submission.id == id:
                    return submission
        raise KeyError(f"no fake submission with id={id!r}")
