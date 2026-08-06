from datetime import datetime, timezone
from pathlib import Path

from backend.reddit.models import AnalyzedPost, RedditPost, RedditResearchReport
from backend.reddit.report import render_markdown_report, save_report_to_knowledge_base

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_report(analyzed_posts=None, **overrides) -> RedditResearchReport:
    defaults = dict(
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
    defaults.update(overrides)
    return RedditResearchReport(**defaults)


def make_post(post_id: str = "p1", subreddit: str = "test", **overrides) -> RedditPost:
    defaults = dict(
        id=post_id,
        subreddit=subreddit,
        title="Why is IoT connectivity so expensive?",
        selftext="We switched away from Emnify but pricing is still confusing.",
        url="https://example.com",
        permalink=f"https://reddit.com/r/{subreddit}/comments/{post_id}",
        author="someone",
        score=42,
        num_comments=3,
        created_utc=NOW,
    )
    defaults.update(overrides)
    return RedditPost(**defaults)


def make_analyzed_post(**overrides) -> AnalyzedPost:
    defaults = dict(
        post=make_post(),
        relevance_score=0.87,
        questions=["Why is IoT connectivity so expensive?"],
        pain_points=["pricing is still confusing"],
        buying_signals=["looking for a cheaper provider"],
        competitor_mentions=["Emnify"],
    )
    defaults.update(overrides)
    return AnalyzedPost(**defaults)


# --- top-level structure -----------------------------------------------


def test_brief_has_professional_headings_in_order() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    headings = ["Executive Summary", "Key Findings", "Customer Pain Points", "Sources"]
    positions = [markdown.index(h) for h in headings]
    assert positions == sorted(positions)


def test_executive_summary_is_prose_not_a_data_dump() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    summary_section = markdown.split("### Executive Summary")[1].split("###")[0]
    assert "We reviewed" in summary_section
    assert "IoT connectivity pricing" in summary_section


def test_relevance_scores_and_comment_counts_are_not_shown() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    assert "0.87" not in markdown
    assert "score 42" not in markdown
    assert "3 comment" not in markdown


def test_sources_and_methodology_are_pushed_to_the_bottom() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    assert markdown.index("Executive Summary") < markdown.index("Sources")
    assert markdown.index("Sources") < markdown.index("Methodology")


def test_source_link_present_in_sources_not_scattered_through_body() -> None:
    markdown = render_markdown_report(make_report([make_analyzed_post()]), "KORE Wireless")
    sources_section = markdown.split("### Sources")[1]
    assert "https://reddit.com/r/test/comments/p1" in sources_section


def test_empty_report_still_professional() -> None:
    markdown = render_markdown_report(make_report([]), "KORE Wireless")
    assert "No discussions scored high enough" in markdown
    assert "Methodology" in markdown


# --- grouping / dedup ------------------------------------------------------


def test_pain_points_from_multiple_posts_are_grouped_under_one_heading() -> None:
    posts = [
        make_analyzed_post(
            post=make_post("p1", "test"),
            pain_points=["reliability is a nightmare"],
            buying_signals=[],
            questions=[],
            competitor_mentions=[],
        ),
        make_analyzed_post(
            post=make_post("p2", "networking"),
            pain_points=["billing is confusing"],
            buying_signals=[],
            questions=[],
            competitor_mentions=[],
        ),
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    assert markdown.count("### Customer Pain Points") == 1
    section = markdown.split("### Customer Pain Points")[1].split("###")[0]
    assert "reliability is a nightmare" in section
    assert "billing is confusing" in section


def test_duplicate_pain_points_across_posts_are_deduplicated() -> None:
    posts = [
        make_analyzed_post(
            post=make_post("p1"), pain_points=["Reliability is a nightmare"],
            buying_signals=[], questions=[], competitor_mentions=[],
        ),
        make_analyzed_post(
            post=make_post("p2"), pain_points=["reliability is a nightmare"],
            buying_signals=[], questions=[], competitor_mentions=[],
        ),
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    section = markdown.split("### Customer Pain Points")[1].split("###")[0]
    assert section.lower().count("reliability is a nightmare") == 1


# --- competitive landscape -------------------------------------------------


def test_competitor_mentions_aggregated_with_counts() -> None:
    posts = [
        make_analyzed_post(post=make_post("p1", "test"), competitor_mentions=["Emnify"]),
        make_analyzed_post(post=make_post("p2", "networking"), competitor_mentions=["Emnify"]),
        make_analyzed_post(post=make_post("p3", "iot"), competitor_mentions=["OtherCo"]),
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    section = markdown.split("### Competitive Landscape")[1].split("###")[0]
    assert "**Emnify** — mentioned 2 times" in section
    assert "**OtherCo** — mentioned 1 time" in section
    # Most-mentioned competitor listed first
    assert section.index("Emnify") < section.index("OtherCo")


def test_no_competitive_landscape_section_when_no_mentions() -> None:
    markdown = render_markdown_report(
        make_report([make_analyzed_post(competitor_mentions=[])]), "KORE Wireless"
    )
    assert "Competitive Landscape" not in markdown


# --- key findings -----------------------------------------------------------


def test_key_findings_capped_and_diverse() -> None:
    posts = [
        make_analyzed_post(
            post=make_post(f"p{i}"),
            pain_points=[f"pain point {i}"],
            buying_signals=[],
            questions=[],
            competitor_mentions=[],
        )
        for i in range(5)
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    key_findings_section = markdown.split("### Key Findings")[1].split("###")[0]
    # capped at 2 pain-point findings even though 5 posts have one
    assert key_findings_section.count("**Pain point:**") == 2


def test_key_findings_prioritizes_highest_relevance_posts_first() -> None:
    posts = [
        make_analyzed_post(post=make_post("p1"), pain_points=["first, most relevant pain point"]),
        make_analyzed_post(post=make_post("p2"), pain_points=["second pain point"]),
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    section = markdown.split("### Key Findings")[1].split("###")[0]
    assert section.index("first, most relevant") < section.index("second pain point")


# --- questions ---------------------------------------------------------------


def test_questions_section_caps_long_lists_with_a_note() -> None:
    posts = [
        make_analyzed_post(
            post=make_post(f"p{i}"),
            questions=[f"Is option {i} any good?"],
            pain_points=[],
            buying_signals=[],
            competitor_mentions=[],
        )
        for i in range(12)
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    section = markdown.split("### Questions From the Community")[1].split("###")[0]
    assert section.count("Is option") == 8
    assert "and 4 more" in section


# --- recurring terms in the executive summary --------------------------------


def test_recurring_terms_surfaced_when_repeated_across_posts() -> None:
    posts = [
        make_analyzed_post(
            post=make_post("p1"), pain_points=["reliability issues are the worst"],
            buying_signals=[], questions=[], competitor_mentions=[],
        ),
        make_analyzed_post(
            post=make_post("p2"), pain_points=["reliability keeps getting worse"],
            buying_signals=[], questions=[], competitor_mentions=[],
        ),
    ]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    summary_section = markdown.split("### Executive Summary")[1].split("###")[0]
    assert "reliability" in summary_section.lower()


def test_no_recurring_terms_line_when_nothing_repeats() -> None:
    posts = [make_analyzed_post(pain_points=["a totally unique complaint here"])]
    markdown = render_markdown_report(make_report(posts), "KORE Wireless")
    summary_section = markdown.split("### Executive Summary")[1].split("###")[0]
    assert "Recurring terms" not in summary_section


# --- knowledge base saving (unchanged behavior) ------------------------------


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
