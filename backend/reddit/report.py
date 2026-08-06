"""Render a `RedditResearchReport` as readable Markdown, and save it into the
client's knowledge base.

This is what makes a research run's output something a marketer can
actually read and reuse — the GUI shows exactly this text, and it's the
same text that lands in ``clients/<slug>/knowledge/reddit.md``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.reddit.models import AnalyzedPost, RedditResearchReport

logger = logging.getLogger(__name__)

PLACEHOLDER_MARKER = "**Status: empty."


def render_markdown_report(report: RedditResearchReport, client_display_name: str) -> str:
    """Render a full research report as Markdown, ready to show or save."""
    lines: list[str] = [
        f"## Reddit Research — \"{report.topic}\" ({report.fetched_at:%Y-%m-%d %H:%M} UTC)",
        "",
        f"**Client:** {client_display_name}  ",
        f"**Queries used:** {', '.join(report.generated_queries)}  ",
        f"**Subreddits:** {', '.join(report.subreddits)}",
        "",
        (
            f"Fetched **{report.total_fetched}** post(s) — "
            f"{report.duplicates_removed} duplicate(s) and {report.spam_removed} "
            f"spam/low-quality removed — **{len(report.analyzed_posts)} kept**."
        ),
        "",
        (
            f"**{report.total_questions}** question(s), "
            f"**{report.total_pain_points}** pain point(s), "
            f"**{report.total_buying_signals}** buying signal(s), "
            f"**{report.total_competitor_mentions}** competitor mention(s)."
        ),
        "",
    ]

    if not report.analyzed_posts:
        lines.append("_No threads scored high enough to include. Try a broader topic._")
        return "\n".join(lines)

    lines.append("### Top threads")
    lines.append("")
    for index, analyzed in enumerate(report.analyzed_posts, start=1):
        lines.extend(_render_post_section(index, analyzed))

    return "\n".join(lines).rstrip() + "\n"


def _render_post_section(index: int, analyzed: AnalyzedPost) -> list[str]:
    post = analyzed.post
    lines = [
        f"#### {index}. {post.title}",
        (
            f"r/{post.subreddit} &middot; score {post.score} &middot; "
            f"{post.num_comments} comment(s) &middot; relevance {analyzed.relevance_score:.2f}  "
        ),
        post.permalink,
        "",
    ]

    for label, items in (
        ("Questions", analyzed.questions),
        ("Pain points", analyzed.pain_points),
        ("Buying signals", analyzed.buying_signals),
    ):
        if items:
            lines.append(f"**{label}:**")
            lines.extend(f"- {item}" for item in items)
            lines.append("")

    if analyzed.competitor_mentions:
        lines.append(f"**Competitor mentions:** {', '.join(analyzed.competitor_mentions)}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return lines


def save_report_to_knowledge_base(clients_dir: Path, client_id: str, report_markdown: str) -> Path:
    """Write ``report_markdown`` into ``clients/<client_id>/knowledge/reddit.md``.

    The scaffolded placeholder ("Status: empty...") is replaced outright on
    the first real run; every run after that appends a new dated section, so
    the file becomes a running research log rather than a single snapshot.
    """
    knowledge_path = clients_dir / client_id / "knowledge" / "reddit.md"
    knowledge_path.parent.mkdir(parents=True, exist_ok=True)

    existing = knowledge_path.read_text(encoding="utf-8") if knowledge_path.is_file() else ""
    is_placeholder = not existing.strip() or PLACEHOLDER_MARKER in existing

    if is_placeholder:
        new_content = "# Reddit Research\n\n" + report_markdown
    else:
        new_content = existing.rstrip() + "\n\n" + report_markdown

    knowledge_path.write_text(new_content, encoding="utf-8")
    logger.info("Saved Reddit research report to %s", knowledge_path)
    return knowledge_path
