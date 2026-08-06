"""Marketing-intelligence analysis pass over raw Reddit search results.

Deliberately heuristic (keyword/lexicon-based), not ML/LLM-based: it's
deterministic, has no external dependency or cost, and is fully unit
testable. `AIService` (still a TODO) is the natural place for a smarter,
Claude-backed version of extraction later — this is the honest v1.

The goal is fewer, better-qualified threads, not more raw posts: every
function here either scores or removes, never invents content.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Sequence
from difflib import SequenceMatcher

from backend.reddit.models import AnalyzedPost, RedditPost

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9']+")
_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?")
_QUESTION_RE = re.compile(r"([^.!?\n]{5,300}\?)")

REMOVED_MARKERS = {"[removed]", "[deleted]", ""}
SPAM_PHRASES = [
    "check out my",
    "dm me",
    "click here",
    "as an ai language model",
    "buy now",
    "limited time offer",
    "subscribe to my",
    "link in bio",
]
MIN_SCORE_THRESHOLD = -5
MAX_LINKS_BEFORE_SPAM = 3
ALL_CAPS_TITLE_RATIO = 0.8
ALL_CAPS_MIN_LETTERS = 8

PAIN_POINT_PHRASES = [
    "frustrated with",
    "frustrating",
    "annoying",
    "hate that",
    "hate when",
    "wish it",
    "wish there was",
    "problem with",
    "issue with",
    "struggling with",
    "struggle with",
    "doesn't work",
    "does not work",
    "can't figure out",
    "cannot figure out",
    "so difficult",
    "so hard to",
    "nightmare to",
    "worst experience",
    "waste of money",
    "waste of time",
    "keeps failing",
    "keeps breaking",
    "unreliable",
]

BUYING_SIGNAL_PHRASES = [
    "looking for a",
    "looking for an",
    "any recommendations for",
    "any recommendation for",
    "should i buy",
    "should i get",
    "worth the money",
    "worth it",
    "considering switching",
    "thinking about switching",
    "about to purchase",
    "in the market for",
    "planning to buy",
    "planning to switch",
    "which one should i",
    "what should i buy",
    "ready to buy",
    "about to sign up",
]

DEFAULT_MIN_RELEVANCE = 0.05
DUPLICATE_TITLE_SIMILARITY_THRESHOLD = 0.9


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _post_text_blocks(post: RedditPost) -> list[str]:
    return [post.title, post.selftext] + [c.body for c in post.top_comments]


def score_relevance(post: RedditPost, topic: str, keywords: Sequence[str] = ()) -> float:
    """Score 0.0-1.0: keyword overlap with the topic/keywords (70%) plus
    engagement (30%, log-scaled so viral outliers don't dominate).
    """
    terms: set[str] = _tokenize(topic)
    for keyword in keywords:
        terms |= _tokenize(keyword)
    if not terms:
        return 0.0

    haystack = _tokenize(f"{post.title} {post.selftext}")
    keyword_score = len(terms & haystack) / len(terms)
    engagement_score = min(1.0, math.log1p(max(0, post.score) + post.num_comments) / math.log1p(200))
    return round(0.7 * keyword_score + 0.3 * engagement_score, 4)


def _normalize_title(title: str) -> str:
    return " ".join(_WORD_RE.findall(title.lower()))


def deduplicate_posts(posts: list[RedditPost]) -> tuple[list[RedditPost], int]:
    """Drop exact-id repeats and near-duplicate titles (cross-posts, reposts)."""
    seen_ids: set[str] = set()
    seen_titles: list[str] = []
    deduped: list[RedditPost] = []
    removed = 0

    for post in posts:
        if post.id in seen_ids:
            removed += 1
            continue
        normalized = _normalize_title(post.title)
        if any(
            SequenceMatcher(None, normalized, other).ratio() >= DUPLICATE_TITLE_SIMILARITY_THRESHOLD
            for other in seen_titles
        ):
            removed += 1
            continue
        seen_ids.add(post.id)
        seen_titles.append(normalized)
        deduped.append(post)

    return deduped, removed


def is_spam(post: RedditPost) -> bool:
    """Heuristic spam/low-quality check: removed content, dead-negative
    score, promotional phrases, link-stuffing, or shouty all-caps titles.
    """
    if post.selftext.strip().lower() in REMOVED_MARKERS and not post.title:
        return True
    if post.score <= MIN_SCORE_THRESHOLD:
        return True

    text = f"{post.title} {post.selftext}".lower()
    if any(phrase in text for phrase in SPAM_PHRASES):
        return True
    if text.count("http://") + text.count("https://") >= MAX_LINKS_BEFORE_SPAM:
        return True

    letters = [c for c in post.title if c.isalpha()]
    if letters and len(letters) > ALL_CAPS_MIN_LETTERS:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > ALL_CAPS_TITLE_RATIO:
            return True

    return False


def filter_spam(posts: list[RedditPost]) -> tuple[list[RedditPost], int]:
    kept = [p for p in posts if not is_spam(p)]
    return kept, len(posts) - len(kept)


def extract_questions(post: RedditPost) -> list[str]:
    """Pull genuine questions (title, body, top comments) — the raw material
    for customer-question research.
    """
    questions: list[str] = []
    for block in _post_text_blocks(post):
        for match in _QUESTION_RE.findall(block or ""):
            cleaned = match.strip()
            if cleaned and cleaned not in questions:
                questions.append(cleaned)
    return questions


def _extract_sentences_matching(post: RedditPost, phrases: Sequence[str]) -> list[str]:
    matches: list[str] = []
    for block in _post_text_blocks(post):
        for sentence in _SENTENCE_RE.findall(block or ""):
            lowered = sentence.lower()
            if any(phrase in lowered for phrase in phrases):
                cleaned = sentence.strip()
                if cleaned and cleaned not in matches:
                    matches.append(cleaned)
    return matches


def extract_pain_points(post: RedditPost) -> list[str]:
    """Sentences matching the pain-point lexicon (frustration, breakage, waste)."""
    return _extract_sentences_matching(post, PAIN_POINT_PHRASES)


def detect_buying_signals(post: RedditPost) -> list[str]:
    """Sentences matching the buying-intent lexicon (recommendations, switching, purchase)."""
    return _extract_sentences_matching(post, BUYING_SIGNAL_PHRASES)


def detect_competitor_mentions(post: RedditPost, competitor_names: Sequence[str]) -> list[str]:
    """Whole-word, case-insensitive match of known competitor names in the post text."""
    text = " ".join([post.title, post.selftext] + [c.body for c in post.top_comments]).lower()
    found: list[str] = []
    for name in competitor_names:
        name = name.strip()
        if not name:
            continue
        if re.search(r"\b" + re.escape(name.lower()) + r"\b", text):
            found.append(name)
    return found


def analyze_posts(
    posts: list[RedditPost],
    topic: str,
    keywords: Sequence[str] = (),
    competitor_names: Sequence[str] = (),
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
) -> tuple[list[AnalyzedPost], int, int]:
    """Run the full quality pass: dedup -> spam filter -> score -> extract.

    Returns ``(analyzed_posts, duplicates_removed, spam_removed)``, sorted by
    relevance score descending. Posts scoring below ``min_relevance`` are
    dropped — the goal is a shorter, higher-signal list, not a longer one.
    """
    deduped, duplicates_removed = deduplicate_posts(posts)
    kept, spam_removed = filter_spam(deduped)

    analyzed: list[AnalyzedPost] = []
    for post in kept:
        relevance = score_relevance(post, topic, keywords)
        if relevance < min_relevance:
            continue
        analyzed.append(
            AnalyzedPost(
                post=post,
                relevance_score=relevance,
                questions=extract_questions(post),
                pain_points=extract_pain_points(post),
                buying_signals=detect_buying_signals(post),
                competitor_mentions=detect_competitor_mentions(post, competitor_names),
            )
        )

    analyzed.sort(key=lambda a: a.relevance_score, reverse=True)
    logger.info(
        "Analyzed %d post(s): %d duplicates removed, %d spam removed, %d below relevance threshold",
        len(posts),
        duplicates_removed,
        spam_removed,
        len(kept) - len(analyzed),
    )
    return analyzed, duplicates_removed, spam_removed
