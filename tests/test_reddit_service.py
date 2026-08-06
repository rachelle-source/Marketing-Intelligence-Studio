import json
from pathlib import Path

from backend.core.database import Database
from backend.reddit.client import RedditClient
from backend.reddit.service import RedditService
from tests.reddit_fakes import FakeComment, FakeCommentForest, FakeReddit, FakeSubmission, FakeSubreddit


def make_service(tmp_path: Path, fake_reddit: FakeReddit) -> tuple[RedditService, Database]:
    db = Database(tmp_path / "test.db")
    db.init_db()

    clients_dir = tmp_path / "clients"
    client_dir = clients_dir / "kore"
    client_dir.mkdir(parents=True)
    (client_dir / "seo.json").write_text(
        json.dumps({"primary_keywords": ["IoT connectivity"]}), encoding="utf-8"
    )
    (client_dir / "competitors.json").write_text(
        json.dumps({"named_competitors": [{"name": "Emnify"}]}), encoding="utf-8"
    )

    reddit_client = RedditClient(reddit=fake_reddit)
    service = RedditService(database=db, clients_dir=clients_dir, client=reddit_client)
    return service, db


def make_fake_reddit_with_posts() -> FakeReddit:
    submission = FakeSubmission(
        id="p1",
        title="Struggling with IoT connectivity reliability, any recommendations?",
        selftext="We moved off Emnify but it's still unreliable.",
        score=25,
        num_comments=1,
        comments=FakeCommentForest([FakeComment(id="c1", body="Have you tried a different carrier?")]),
    )
    return FakeReddit({"all": FakeSubreddit("all", [submission])})


def test_research_returns_structured_report(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    report = service.research("kore", "IoT connectivity")

    assert report.client_id == "kore"
    assert report.topic == "IoT connectivity"
    assert report.total_fetched >= 1
    assert report.analyzed_posts
    assert report.total_competitor_mentions >= 1
    assert "IoT connectivity" in report.generated_queries


def test_run_reddit_research_persists_session(tmp_path: Path) -> None:
    service, db = make_service(tmp_path, make_fake_reddit_with_posts())
    session = service.run_reddit_research("kore", "IoT connectivity")

    assert session.client_id == "kore"
    assert session.source_type == "reddit"
    assert "relevant post" in session.summary

    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM research_sessions WHERE id = ?", (session.id,)
        ).fetchone()
    assert row is not None
    assert row["client_id"] == "kore"


def test_run_reddit_research_creates_client_row_if_missing(tmp_path: Path) -> None:
    service, db = make_service(tmp_path, make_fake_reddit_with_posts())
    service.run_reddit_research("kore", "IoT connectivity")

    with db.connect() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", ("kore",)).fetchone()
    assert row is not None


def test_list_sessions_returns_saved_sessions_newest_first(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    service.run_reddit_research("kore", "topic one")
    service.run_reddit_research("kore", "topic two")

    sessions = service.list_sessions("kore")
    assert len(sessions) == 2
    assert {s.query for s in sessions} == {"topic one", "topic two"}


def test_list_sessions_empty_for_unknown_client(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    assert service.list_sessions("nobody") == []
