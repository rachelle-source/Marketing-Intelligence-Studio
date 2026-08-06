import pytest

from backend.reddit.client import RedditClient
from backend.reddit.errors import RedditCredentialsError
from tests.reddit_fakes import (
    FakeComment,
    FakeCommentForest,
    FakeReddit,
    FakeSubmission,
    FakeSubreddit,
)


def test_missing_credentials_raises_structured_error(monkeypatch) -> None:
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    client = RedditClient()
    with pytest.raises(RedditCredentialsError):
        client.search_posts("test query")


def test_injected_fake_reddit_bypasses_credentials() -> None:
    fake = FakeReddit()
    client = RedditClient(reddit=fake)
    posts = client.search_posts("anything", subreddits=["test"])
    assert posts == []


def test_search_posts_normalizes_submission_without_fetching_comments() -> None:
    submission = FakeSubmission(
        id="p1",
        title="How do I fix this?",
        selftext="Body text here",
        score=42,
        num_comments=1,
        subreddit="learnpython",
    )
    fake = FakeReddit({"learnpython": FakeSubreddit("learnpython", [submission])})

    client = RedditClient(reddit=fake)
    posts = client.search_posts("fix", subreddits=["learnpython"], post_limit=5)

    assert len(posts) == 1
    post = posts[0]
    assert post.id == "p1"
    assert post.subreddit == "learnpython"
    assert post.title == "How do I fix this?"
    assert post.score == 42
    assert post.top_comments == []  # search_posts never fetches comments — see fetch_top_comments
    assert post.permalink.startswith("https://reddit.com")


def test_search_posts_across_multiple_subreddits() -> None:
    sub_a = FakeSubreddit("a", [FakeSubmission(id="a1", title="A post")])
    sub_b = FakeSubreddit("b", [FakeSubmission(id="b1", title="B post")])
    fake = FakeReddit({"a": sub_a, "b": sub_b})

    client = RedditClient(reddit=fake)
    posts = client.search_posts("q", subreddits=["a", "b"])

    assert {p.id for p in posts} == {"a1", "b1"}


def test_defaults_to_all_subreddit_when_none_given() -> None:
    fake = FakeReddit({"all": FakeSubreddit("all", [FakeSubmission(id="x1", title="X")])})
    client = RedditClient(reddit=fake)
    posts = client.search_posts("q")
    assert posts[0].id == "x1"


# --- fetch_top_comments ---


def test_fetch_top_comments_returns_normalized_comments() -> None:
    comments = FakeCommentForest([FakeComment(id="c1", body="A top comment", score=5)])
    submission = FakeSubmission(id="p1", title="Title", comments=comments)
    fake = FakeReddit({"test": FakeSubreddit("test", [submission])})

    client = RedditClient(reddit=fake)
    result = client.fetch_top_comments("p1", comment_limit=5)

    assert len(result) == 1
    assert result[0].body == "A top comment"
    assert result[0].score == 5


def test_fetch_top_comments_respects_limit() -> None:
    comments = FakeCommentForest([FakeComment(id=f"c{i}", body=f"comment {i}") for i in range(5)])
    submission = FakeSubmission(id="p1", title="Title", comments=comments)
    fake = FakeReddit({"test": FakeSubreddit("test", [submission])})

    client = RedditClient(reddit=fake)
    result = client.fetch_top_comments("p1", comment_limit=2)

    assert len(result) == 2


def test_fetch_top_comments_zero_limit_skips_fetch_entirely() -> None:
    fake = FakeReddit()
    client = RedditClient(reddit=fake)
    assert client.fetch_top_comments("does-not-matter", comment_limit=0) == []
