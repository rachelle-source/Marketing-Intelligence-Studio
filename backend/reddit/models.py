"""Normalized internal data model for Reddit research.

Everything downstream (analysis, the research pipeline, storage) works with
these models — never with raw PRAW objects — so PRAW stays an implementation
detail confined to `backend.reddit.client`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.models._shared import utcnow


class RedditComment(BaseModel):
    """A single top-level comment on a Reddit post."""

    id: str
    author: str | None = None
    body: str
    score: int
    created_utc: datetime


class RedditPost(BaseModel):
    """A single Reddit post (submission), with its top-level comments."""

    id: str
    subreddit: str
    title: str
    selftext: str = ""
    url: str
    permalink: str
    author: str | None = None
    score: int
    num_comments: int
    created_utc: datetime
    top_comments: list[RedditComment] = Field(default_factory=list)


class RedditSearchResult(BaseModel):
    """Raw, normalized output of a Reddit search — no filtering or scoring applied."""

    query: str
    subreddits: list[str]
    posts: list[RedditPost]
    fetched_at: datetime = Field(default_factory=utcnow)


class AnalyzedPost(BaseModel):
    """A post enriched with the marketing-intelligence analysis pass.

    Only posts that survived spam filtering and deduplication ever become an
    ``AnalyzedPost`` — there is no ``is_spam`` flag here because spam/duplicate
    posts are dropped before this stage, not tagged and kept.
    """

    post: RedditPost
    relevance_score: float
    questions: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    competitor_mentions: list[str] = Field(default_factory=list)


class RedditResearchReport(BaseModel):
    """Full structured output of a research run, for the research pipeline."""

    client_id: str
    topic: str
    generated_queries: list[str]
    subreddits: list[str]
    total_fetched: int
    duplicates_removed: int
    spam_removed: int
    analyzed_posts: list[AnalyzedPost]
    fetched_at: datetime = Field(default_factory=utcnow)

    @property
    def total_questions(self) -> int:
        return sum(len(p.questions) for p in self.analyzed_posts)

    @property
    def total_pain_points(self) -> int:
        return sum(len(p.pain_points) for p in self.analyzed_posts)

    @property
    def total_buying_signals(self) -> int:
        return sum(len(p.buying_signals) for p in self.analyzed_posts)

    @property
    def total_competitor_mentions(self) -> int:
        return sum(len(p.competitor_mentions) for p in self.analyzed_posts)
