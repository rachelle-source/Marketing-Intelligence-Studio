import json
from pathlib import Path

import pytest

from backend.core.database import Database
from backend.reddit.client import RedditClient
from backend.reddit.errors import RedditSearchError
from backend.reddit.service import RedditService
from tests.reddit_fakes import FakeComment, FakeCommentForest, FakeReddit, FakeSubmission, FakeSubreddit


def make_service(tmp_path: Path, fake_reddit: FakeReddit) -> tuple[RedditService, Database, Path]:
    db = Database(tmp_path / "test.db")
    db.init_db()

    clients_dir = tmp_path / "clients"
    client_dir = clients_dir / "kore"
    client_dir.mkdir(parents=True)
    (client_dir / "knowledge").mkdir()
    (client_dir / "profile.json").write_text(
        json.dumps({"client_name": "KORE Wireless"}), encoding="utf-8"
    )
    (client_dir / "seo.json").write_text(
        json.dumps({"primary_keywords": ["IoT connectivity"]}), encoding="utf-8"
    )
    (client_dir / "competitors.json").write_text(
        json.dumps({"named_competitors": [{"name": "Emnify"}]}), encoding="utf-8"
    )
    (client_dir / "knowledge" / "reddit.md").write_text(
        "# KORE Wireless — Reddit Research\n\n**Status: empty.** No Reddit research has been run.\n",
        encoding="utf-8",
    )

    reddit_client = RedditClient(reddit=fake_reddit)
    service = RedditService(database=db, clients_dir=clients_dir, client=reddit_client)
    return service, db, clients_dir


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
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    report = service.research("kore", "IoT connectivity")

    assert report.client_id == "kore"
    assert report.topic == "IoT connectivity"
    assert report.total_fetched >= 1
    assert report.analyzed_posts
    assert report.total_competitor_mentions >= 1
    assert "IoT connectivity" in report.generated_queries


def test_research_fetches_comments_only_for_kept_posts(tmp_path: Path) -> None:
    """The comments attached to fake submissions should still make it into
    the final report — proving the deferred fetch-comments-for-top-N-only
    path (search_posts -> rank -> fetch_top_comments) actually wires the
    comments back onto the winning posts.
    """
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    report = service.research("kore", "IoT connectivity")

    top_post = report.analyzed_posts[0].post
    assert len(top_post.top_comments) == 1
    assert top_post.top_comments[0].body == "Have you tried a different carrier?"


def test_research_caps_at_max_results(tmp_path: Path) -> None:
    # Distinct topics per post (not just a trailing number) so the
    # near-duplicate-title dedup doesn't collapse them before max_results
    # ever gets a chance to apply.
    topics = [
        "pricing",
        "reliability",
        "coverage",
        "setup",
        "billing",
        "support",
        "outages",
        "roaming",
        "hardware",
        "security",
        "latency",
        "compliance",
        "logistics",
        "onboarding",
        "integration",
    ]
    submissions = [
        FakeSubmission(
            id=f"p{i}",
            title=f"IoT connectivity {topic} question from a customer",
            score=10 + i,
        )
        for i, topic in enumerate(topics)
    ]
    fake = FakeReddit({"all": FakeSubreddit("all", submissions)})
    service, _, _ = make_service(tmp_path, fake)

    report = service.research("kore", "IoT connectivity", max_results=5)
    assert len(report.analyzed_posts) <= 5


def test_one_failing_query_does_not_abort_the_whole_run(tmp_path: Path, monkeypatch) -> None:
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())

    real_search = service._client.search_posts
    call_count = {"n": 0}

    def flaky_search(query, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RedditSearchError("simulated transient failure")
        return real_search(query, **kwargs)

    monkeypatch.setattr(service._client, "search_posts", flaky_search)

    report = service.research("kore", "IoT connectivity")
    assert call_count["n"] >= 2  # more than one query was attempted
    assert report.total_fetched >= 1  # the later, successful query still contributed posts


def test_all_queries_failing_raises_structured_error(tmp_path: Path, monkeypatch) -> None:
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())

    def always_fails(query, **kwargs):  # noqa: ARG001
        raise RedditSearchError("simulated total outage")

    monkeypatch.setattr(service._client, "search_posts", always_fails)

    with pytest.raises(RedditSearchError):
        service.research("kore", "IoT connectivity")


def test_run_and_report_returns_session_and_markdown(tmp_path: Path) -> None:
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    session, markdown = service.run_and_report("kore", "IoT connectivity")

    assert session.client_id == "kore"
    assert "Reddit Research" in markdown
    assert "IoT connectivity" in markdown


def test_run_and_report_saves_to_knowledge_base(tmp_path: Path) -> None:
    service, _, clients_dir = make_service(tmp_path, make_fake_reddit_with_posts())
    service.run_and_report("kore", "IoT connectivity")

    knowledge_file = clients_dir / "kore" / "knowledge" / "reddit.md"
    content = knowledge_file.read_text(encoding="utf-8")
    assert "Status: empty" not in content
    assert "IoT connectivity" in content


def test_run_reddit_research_persists_session(tmp_path: Path) -> None:
    service, db, _ = make_service(tmp_path, make_fake_reddit_with_posts())
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
    service, db, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    service.run_reddit_research("kore", "IoT connectivity")

    with db.connect() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", ("kore",)).fetchone()
    assert row is not None


def test_list_sessions_returns_saved_sessions_newest_first(tmp_path: Path) -> None:
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    service.run_reddit_research("kore", "topic one")
    service.run_reddit_research("kore", "topic two")

    sessions = service.list_sessions("kore")
    assert len(sessions) == 2
    assert {s.query for s in sessions} == {"topic one", "topic two"}


def test_list_sessions_empty_for_unknown_client(tmp_path: Path) -> None:
    service, _, _ = make_service(tmp_path, make_fake_reddit_with_posts())
    assert service.list_sessions("nobody") == []
