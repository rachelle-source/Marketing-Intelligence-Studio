import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Thread, ClientConfig
import scrape


@pytest.fixture
def mock_config():
    return ClientConfig(
        client_name="TestClient",
        subreddits=["solar"],
        keywords=["solar"],
        brand_context="Test context",
        notify_email="test@test.com",
        max_threads=5,
        sort="hot",
    )


@pytest.fixture
def mock_threads():
    return [
        Thread(
            title="Is solar worth it in NC?",
            body="Thinking about going solar.",
            url="https://reddit.com/r/solar/1",
            upvotes=42,
            num_comments=8,
            subreddit="solar",
            created_utc=1700000000.0,
        )
    ]


def test_json_out_writes_file(tmp_path, mock_config, mock_threads):
    out_file = str(tmp_path / "threads.json")
    with patch("scrape.load_config", return_value=mock_config), \
         patch("scrape.fetch_all_threads", return_value=mock_threads):
        scrape.scrape_one("8msolar", json_out=out_file)

    data = json.loads(Path(out_file).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["title"] == "Is solar worth it in NC?"
    assert data[0]["subreddit"] == "solar"
    assert data[0]["upvotes"] == 42


def test_json_out_includes_all_thread_fields(tmp_path, mock_config, mock_threads):
    out_file = str(tmp_path / "threads.json")
    with patch("scrape.load_config", return_value=mock_config), \
         patch("scrape.fetch_all_threads", return_value=mock_threads):
        scrape.scrape_one("8msolar", json_out=out_file)

    data = json.loads(Path(out_file).read_text(encoding="utf-8"))
    expected_keys = {"title", "body", "url", "upvotes", "num_comments", "subreddit", "created_utc"}
    assert set(data[0].keys()) == expected_keys


def test_json_out_creates_parent_dirs(tmp_path, mock_config, mock_threads):
    out_file = str(tmp_path / "nested" / "dir" / "threads.json")
    with patch("scrape.load_config", return_value=mock_config), \
         patch("scrape.fetch_all_threads", return_value=mock_threads):
        scrape.scrape_one("8msolar", json_out=out_file)

    assert Path(out_file).exists()


def test_json_out_multiple_threads(tmp_path, mock_config):
    threads = [
        Thread(title=f"Thread {i}", body="body", url=f"https://reddit.com/{i}",
               upvotes=i, num_comments=i, subreddit="solar", created_utc=float(i))
        for i in range(3)
    ]
    out_file = str(tmp_path / "threads.json")
    with patch("scrape.load_config", return_value=mock_config), \
         patch("scrape.fetch_all_threads", return_value=threads):
        scrape.scrape_one("8msolar", json_out=out_file)

    data = json.loads(Path(out_file).read_text(encoding="utf-8"))
    assert len(data) == 3


def test_json_out_empty_threads_does_not_write_file(tmp_path, mock_config):
    out_file = str(tmp_path / "threads.json")
    with patch("scrape.load_config", return_value=mock_config), \
         patch("scrape.fetch_all_threads", return_value=[]):
        scrape.scrape_one("8msolar", json_out=out_file)

    assert not Path(out_file).exists()
