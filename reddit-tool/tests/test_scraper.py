import pytest
from unittest.mock import patch, MagicMock
from src.scraper import fetch_threads, fetch_all_threads
from src.models import Thread

MOCK_REDDIT_RESPONSE = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "Best solar panels for a 2000sqft home?",
                    "selftext": "Looking for recommendations on solar panels.",
                    "permalink": "/r/solar/comments/abc123/best_solar/",
                    "score": 42,
                    "created_utc": 1712000000.0,
                    "subreddit": "solar",
                    "num_comments": 15,
                    "stickied": False,
                }
            },
            {
                "data": {
                    "title": "Stickied mod post",
                    "selftext": "",
                    "permalink": "/r/solar/comments/sticky/",
                    "score": 1,
                    "created_utc": 1712000000.0,
                    "subreddit": "solar",
                    "num_comments": 0,
                    "stickied": True,
                }
            }
        ]
    }
}

@patch("src.scraper.requests.get")
def test_fetch_threads_returns_thread_objects(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_REDDIT_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    threads = fetch_threads("solar", sort="hot", limit=10)

    assert len(threads) == 1  # stickied post filtered out
    assert isinstance(threads[0], Thread)
    assert threads[0].title == "Best solar panels for a 2000sqft home?"
    assert threads[0].subreddit == "solar"
    assert threads[0].url == "https://reddit.com/r/solar/comments/abc123/best_solar/"

@patch("src.scraper.requests.get")
def test_fetch_threads_filters_stickied(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_REDDIT_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    threads = fetch_threads("solar")
    titles = [t.title for t in threads]
    assert "Stickied mod post" not in titles

@patch("src.scraper.fetch_threads")
@patch("src.scraper.time.sleep")
def test_fetch_all_threads_calls_each_subreddit(mock_sleep, mock_fetch):
    mock_fetch.return_value = [Thread("t", "b", "u", 1, 1.0, "solar", 1)]

    results = fetch_all_threads(["solar", "solarenergy"], sort="hot", limit=10)

    assert mock_fetch.call_count == 2
    assert mock_sleep.call_count == 2  # rate limit delay called for each
    assert len(results) == 2

@patch("src.scraper.requests.get")
def test_fetch_threads_uses_correct_url(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"children": []}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    fetch_threads("solar", sort="new", limit=5)

    call_url = mock_get.call_args[0][0]
    assert "r/solar/new.json" in call_url
    assert "limit=5" in call_url
