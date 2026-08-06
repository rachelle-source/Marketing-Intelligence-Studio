"""Live Reddit integration test — NOT run automatically.

This hits the real Reddit API through PRAW and needs valid credentials. It
is automatically skipped unless REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
are set — which they never are in CI or in the sandbox this project was
built in (that sandbox's network policy explicitly blocks reddit.com).

## Running this on a developer machine

1. Create a Reddit "script" app at https://www.reddit.com/prefs/apps
   (any Reddit account works; no special permissions needed for read-only
   search).
2. Export credentials:

    export REDDIT_CLIENT_ID="your client id"
    export REDDIT_CLIENT_SECRET="your client secret"
    export REDDIT_USER_AGENT="marketing-intelligence-studio/0.1 by u/<your-username>"

3. Run just this test:

    pytest tests/integration/test_reddit_live.py -v -m integration

It makes a small number of real, read-only requests (a handful of posts
from r/learnpython, a stable and low-traffic-risk subreddit for a smoke
test) — nothing is posted, voted, or modified.
"""

from __future__ import annotations

import os

import pytest

from backend.reddit.client import RedditClient

pytestmark = pytest.mark.integration

_REQUIRED_ENV = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET")
_HAS_CREDENTIALS = all(os.environ.get(name) for name in _REQUIRED_ENV)


@pytest.mark.skipif(
    not _HAS_CREDENTIALS,
    reason="Real Reddit API credentials not set (REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET) "
    "— see this file's module docstring to run it for real.",
)
def test_search_posts_against_live_reddit() -> None:
    client = RedditClient()
    posts = client.search_posts("python", subreddits=["learnpython"], post_limit=3, comment_limit=2)

    assert isinstance(posts, list)
    assert len(posts) <= 3
    for post in posts:
        assert post.id
        assert post.subreddit.lower() == "learnpython"
        assert post.title
