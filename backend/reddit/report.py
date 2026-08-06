"""Render a `RedditResearchReport` as a professional market research brief,
and save it into the client's knowledge base.

This is the actual deliverable — what a marketing strategist reads and
could send to a client. It leads with synthesis (an executive summary and a
handful of top findings), groups similar findings together by category
(all pain points together, all buying signals together, etc.) instead of
repeating the same structure once per thread, and pushes technical detail
(relevance scores, subreddit/comment metadata, source links, the queries
used) down into a compact "Sources" and "Methodology" footer.

Every sentence in the brief is copied or lightly counted/grouped from real
extracted data (`backend.reddit.analysis`) — nothing here is generated or
invented; there's no LLM in this pipeline yet (`AIService` is still a
TODO). "Recurring terms" and "top competitor" are the only two derived
statistics, and both are plain word/mention counts, not judgment calls.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path

from backend.reddit.models import AnalyzedPost, RedditResearchReport

logger = logging.getLogger(__name__)

PLACEHOLDER_MARKER = "**Status: empty."

MAX_KEY_FINDINGS = 5
MAX_KEY_FINDINGS_PER_CATEGORY = 2
MAX_QUESTIONS_SHOWN = 8
MAX_RECURRING_TERMS = 3
MIN_RECURRING_TERM_MENTIONS = 2

_WORD_RE = re.compile(r"[a-z']{4,}")
_STOPWORDS = {
    "this", "that", "these", "those", "with", "from", "have", "haven",
    "just", "very", "about", "into", "your", "their", "they", "them",
    "there", "here", "some", "any", "all", "each", "other", "such", "same",
    "still", "really", "only", "more", "than", "then", "when", "what",
    "which", "whom", "because", "does", "doesn", "didn", "isn", "wasn",
    "were", "been", "being", "would", "could", "should", "will", "cant",
    "dont", "wont", "youre", "want", "wants", "need", "needs",
    "like", "know", "think", "even", "much", "many", "also", "over",
    "used", "using", "trying", "getting", "actually",
}


def render_markdown_report(report: RedditResearchReport, client_display_name: str) -> str:
    """Render a full research report as a market-research-brief-style Markdown document."""
    posts = report.analyzed_posts

    lines: list[str] = [
        f"## Reddit Research Brief — \"{report.topic}\"",
        f"_Prepared for {client_display_name} · {report.fetched_at:%B %d, %Y}_",
        "",
    ]

    if not posts:
        lines.append(
            "**No discussions scored high enough to report on.** Try a broader topic, "
            "or one closer to the client's core keywords."
        )
        lines.append("")
        lines.extend(_render_methodology(report))
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(_render_executive_summary(report))
    lines.extend(_render_key_findings(posts, report.topic))
    lines.extend(_render_grouped_section("Customer Pain Points", _collect(posts, "pain_points")))
    lines.extend(
        _render_grouped_section("Buying Signals & Purchase Intent", _collect(posts, "buying_signals"))
    )
    lines.extend(_render_competitive_landscape(posts))
    lines.extend(_render_questions(posts))
    lines.extend(_render_sources(posts))
    lines.extend(_render_methodology(report))

    return "\n".join(lines).rstrip() + "\n"


# --- Executive Summary -------------------------------------------------


def _render_executive_summary(report: RedditResearchReport) -> list[str]:
    posts = report.analyzed_posts
    sentences = [
        f"We reviewed **{len(posts)}** relevant Reddit discussion(s) about "
        f'"{report.topic}" and identified {report.total_pain_points} pain point(s), '
        f"{report.total_buying_signals} buying signal(s), and "
        f"{report.total_competitor_mentions} competitor mention(s)."
    ]

    top_competitor = _top_competitor(posts)
    if top_competitor:
        name, count = top_competitor
        sentences.append(
            f"**{name}** was the most-discussed competitor, coming up in "
            f"{count} of the discussions reviewed."
        )

    terms = _recurring_terms(posts)
    if terms:
        sentences.append(f"Recurring terms across these discussions include: {', '.join(terms)}.")

    return ["### Executive Summary", "", " ".join(sentences), ""]


# --- Key Findings --------------------------------------------------------


def _render_key_findings(posts: list[AnalyzedPost], topic: str) -> list[str]:  # noqa: ARG001
    findings = _select_key_findings(posts)
    if not findings:
        return []
    lines = ["### Key Findings", ""]
    lines.extend(f"- {finding}" for finding in findings)
    lines.append("")
    return lines


def _select_key_findings(posts: list[AnalyzedPost]) -> list[str]:
    """Pick up to MAX_KEY_FINDINGS standout items, capped per category for
    variety, walking posts in the order given (already relevance-ranked —
    see `select_top_posts`) so the most relevant threads' findings surface
    first.
    """
    findings: list[str] = []
    category_counts: Counter[str] = Counter()

    def add(category: str, label: str, text: str, subreddit: str) -> bool:
        if len(findings) >= MAX_KEY_FINDINGS:
            return False
        if category_counts[category] >= MAX_KEY_FINDINGS_PER_CATEGORY:
            return False
        findings.append(f'**{label}:** "{text}" — r/{subreddit}')
        category_counts[category] += 1
        return True

    for analyzed in posts:
        if len(findings) >= MAX_KEY_FINDINGS:
            break
        subreddit = analyzed.post.subreddit
        if analyzed.pain_points:
            add("pain_point", "Pain point", analyzed.pain_points[0], subreddit)
        if analyzed.buying_signals:
            add("buying_signal", "Buying signal", analyzed.buying_signals[0], subreddit)
        if analyzed.competitor_mentions:
            names = ", ".join(analyzed.competitor_mentions)
            add("competitor", "Competitor mentioned", names, subreddit)
        if analyzed.questions and not analyzed.pain_points and not analyzed.buying_signals:
            add("question", "Notable question", analyzed.questions[0], subreddit)

    return findings[:MAX_KEY_FINDINGS]


# --- Grouped sections (pain points / buying signals) ---------------------


def _collect(posts: list[AnalyzedPost], attr: str) -> list[tuple[str, str]]:
    """Return [(text, subreddit), ...] for every item in `attr` across all
    posts, deduplicated (case-insensitive, exact match) while preserving the
    relevance-ranked order they were found in.
    """
    seen: set[str] = set()
    items: list[tuple[str, str]] = []
    for analyzed in posts:
        for text in getattr(analyzed, attr):
            key = text.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            items.append((text, analyzed.post.subreddit))
    return items


def _render_grouped_section(title: str, items: list[tuple[str, str]]) -> list[str]:
    if not items:
        return []
    lines = [f"### {title}", ""]
    lines.extend(f'- "{text}" — r/{subreddit}' for text, subreddit in items)
    lines.append("")
    return lines


# --- Competitive Landscape ------------------------------------------------


def _competitor_mentions(posts: list[AnalyzedPost]) -> dict[str, list[str]]:
    """Map competitor name -> list of subreddits where it was mentioned."""
    mentions: dict[str, list[str]] = {}
    for analyzed in posts:
        for name in analyzed.competitor_mentions:
            mentions.setdefault(name, []).append(analyzed.post.subreddit)
    return mentions


def _top_competitor(posts: list[AnalyzedPost]) -> tuple[str, int] | None:
    mentions = _competitor_mentions(posts)
    if not mentions:
        return None
    name, subreddits = max(mentions.items(), key=lambda pair: len(pair[1]))
    return name, len(subreddits)


def _render_competitive_landscape(posts: list[AnalyzedPost]) -> list[str]:
    mentions = _competitor_mentions(posts)
    if not mentions:
        return []
    lines = ["### Competitive Landscape", ""]
    for name, subreddits in sorted(mentions.items(), key=lambda pair: len(pair[1]), reverse=True):
        count = len(subreddits)
        where = ", ".join(f"r/{s}" for s in dict.fromkeys(subreddits))
        times = "time" if count == 1 else "times"
        lines.append(f"- **{name}** — mentioned {count} {times} ({where})")
    lines.append("")
    return lines


# --- Questions -------------------------------------------------------------


def _render_questions(posts: list[AnalyzedPost]) -> list[str]:
    items = _collect(posts, "questions")
    if not items:
        return []
    shown, remaining = items[:MAX_QUESTIONS_SHOWN], items[MAX_QUESTIONS_SHOWN:]
    lines = ["### Questions From the Community", ""]
    lines.extend(f'- "{text}" — r/{subreddit}' for text, subreddit in shown)
    if remaining:
        lines.append(f"- _...and {len(remaining)} more (see Sources for the full discussions)_")
    lines.append("")
    return lines


# --- Sources & Methodology (technical detail, pushed to the bottom) ------


def _render_sources(posts: list[AnalyzedPost]) -> list[str]:
    lines = ["### Sources", ""]
    for index, analyzed in enumerate(posts, start=1):
        post = analyzed.post
        lines.append(f"{index}. [{post.title}]({post.permalink}) — r/{post.subreddit}")
    lines.append("")
    return lines


def _render_methodology(report: RedditResearchReport) -> list[str]:
    return [
        "---",
        "",
        (
            f"_Methodology: {report.total_fetched} discussion(s) found across "
            f"{len(report.generated_queries)} search variant(s) of \"{report.topic}\" "
            f"({', '.join(report.subreddits)}); {report.duplicates_removed} duplicate(s) "
            f"and {report.spam_removed} low-quality/spam thread(s) removed before analysis._"
        ),
    ]


# --- Recurring terms (pooled word-frequency over pain points + buying signals) ---


def _recurring_terms(posts: list[AnalyzedPost]) -> list[str]:
    texts = [text for text, _ in _collect(posts, "pain_points")]
    texts += [text for text, _ in _collect(posts, "buying_signals")]

    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(set(_WORD_RE.findall(text.lower())) - _STOPWORDS)

    recurring = [word for word, count in counts.most_common() if count >= MIN_RECURRING_TERM_MENTIONS]
    return recurring[:MAX_RECURRING_TERMS]


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
