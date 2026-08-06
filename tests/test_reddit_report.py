from datetime import datetime, timezone
from pathlib import Path

from backend.reddit.models import AnalyzedPost, RedditPost, RedditResearchReport
from backend.reddit.report import render_markdown_report, save_report_to_knowledge_base

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_report(analyzed_posts=None) -> RedditResearchReport:
    return RedditResearchReport(
        client_id="kore",
        topic="IoT connectivity pricing",
        generated_queries=["IoT connectivity pricing", "IoT connectivity pricing IoT connectivity"],
        subreddits=["all"],
        total_fetched=12,
        duplicates_removed=2,
        spam_removed=3,
        analyzed_posts=analyzed_posts or [],
        fetched_at=NOW,
    )


def make_analyzed_post() -> AnalyzedPost:
    post = RedditPost(
        id="p1",
        subreddit="test",
        title="Why is IoT connectivity so expensive?",
        selftext="We switched away from Emnify but pricing is still confusing.",
        url="https://example.com",
        permalink="https://reddit.com/r/test/comments/p1",
        author="someone",
        score=42,
        num_comments=3,
        created_utc=NOW,
    )
    return AnalyzedPost(
        post=post,
        relevance_score=0.87,
        questions=["Why is IoT connectivity so expensive?"],
        pain_points=["pricing is still confusing"],
        buying_signals=["looking for a cheaper provider"],
        competitor_mentions=["Emnify"],
    )


def test_render_includes_summary_counts() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    assert "KORE Wireless" in markdown
    assert "IoT connectivity pricing" in markdown
    assert "12" in markdown  # total_fetched
    assert "1**" in markdown or "**1" in markdown  # some count renders as 1


def test_render_includes_post_details() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    assert "Why is IoT connectivity so expensive?" in markdown
    assert "r/test" in markdown
    assert "Emnify" in markdown
    assert "pricing is still confusing" in markdown
    assert "looking for a cheaper provider" in markdown
    assert "https://reddit.com/r/test/comments/p1" in markdown


def test_render_empty_report_says_so_without_crashing() -> None:
    markdown = render_markdown_report(make_report([]), "KORE Wireless")
    assert "No threads scored high enough" in markdown


def test_save_replaces_placeholder_on_first_run(tmp_path: Path) -> None:
    client_dir = tmp_path / "kore" / "knowledge"
    client_dir.mkdir(parents=True)
    placeholder = (
        "# KORE Wireless — Reddit Research\n\n"
        "**Status: empty.** No Reddit research has been run for this client.\n"
    )
    (client_dir / "reddit.md").write_text(placeholder, encoding="utf-8")

    report_markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    path = save_report_to_knowledge_base(tmp_path, "kore", report_markdown)

    content = path.read_text(encoding="utf-8")
    assert "Status: empty" not in content
    assert "IoT connectivity pricing" in content


def test_save_appends_on_subsequent_runs(tmp_path: Path) -> None:
    report_markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")

    save_report_to_knowledge_base(tmp_path, "kore", report_markdown)
    path = save_report_to_knowledge_base(tmp_path, "kore", report_markdown)

    content = path.read_text(encoding="utf-8")
    assert content.count("IoT connectivity pricing") >= 2


def test_save_creates_knowledge_dir_if_missing(tmp_path: Path) -> None:
    report_markdown = render_markdown_report(make_report([]), "KORE Wireless")
    path = save_report_to_knowledge_base(tmp_path, "brand-new-client", report_markdown)
    assert path.is_file()
