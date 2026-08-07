import time
import requests
from src.models import Thread

HEADERS = {"User-Agent": "KeystoneRedditTool/1.0 (internal agency tool)"}
RATE_LIMIT_DELAY = 1.5  # seconds between requests


def fetch_threads(subreddit: str, sort: str = "hot", limit: int = 25) -> list[Thread]:
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    posts = response.json()["data"]["children"]

    return [
        Thread(
            title=p["data"]["title"],
            body=p["data"]["selftext"],
            url=f"https://reddit.com{p['data']['permalink']}",
            upvotes=p["data"]["score"],
            created_utc=p["data"]["created_utc"],
            subreddit=subreddit,
            num_comments=p["data"]["num_comments"],
        )
        for p in posts
        if not p["data"]["stickied"]
    ]


def fetch_all_threads(subreddits: list[str], sort: str = "hot", limit: int = 25) -> list[Thread]:
    all_threads = []
    for subreddit in subreddits:
        time.sleep(RATE_LIMIT_DELAY)
        threads = fetch_threads(subreddit, sort=sort, limit=limit)
        all_threads.extend(threads)
    return all_threads
