from datetime import datetime, timezone

from backend.reddit.analysis import (
    analyze_posts,
    deduplicate_posts,
    detect_buying_signals,
    detect_competitor_mentions,
    extract_pain_points,
    extract_questions,
    filter_spam,
    is_spam,
    score_relevance,
)
from backend.reddit.models import RedditComment, RedditPost

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_post(**overrides) -> RedditPost:
    defaults = dict(
        id="p1",
        subreddit="test",
        title="A post",
        selftext="",
        url="https://example.com",
        permalink="https://reddit.com/r/test/comments/p1",
        author="someone",
        score=10,
        num_comments=0,
        created_utc=NOW,
        top_comments=[],
    )
    defaults.update(overrides)
    return RedditPost(**defaults)


def make_comment(**overrides) -> RedditComment:
    defaults = dict(id="c1", author="someone", body="a comment", score=1, created_utc=NOW)
    defaults.update(overrides)
    return RedditComment(**defaults)


# --- score_relevance ---


def test_relevance_scores_higher_for_keyword_overlap() -> None:
    on_topic = make_post(title="IoT connectivity pricing questions", score=5)
    off_topic = make_post(title="My cat is cute", score=5)
    assert score_relevance(on_topic, "IoT connectivity pricing") > score_relevance(
        off_topic, "IoT connectivity pricing"
    )


def test_relevance_is_zero_with_no_terms() -> None:
    assert score_relevance(make_post(), "") == 0.0


def test_relevance_considers_engagement() -> None:
    low_engagement = make_post(title="topic", score=0, num_comments=0)
    high_engagement = make_post(title="topic", score=500, num_comments=200)
    assert score_relevance(high_engagement, "topic") > score_relevance(low_engagement, "topic")


# --- deduplicate_posts ---


def test_dedup_removes_exact_id_repeats() -> None:
    post = make_post(id="p1")
    deduped, removed = deduplicate_posts([post, post])
    assert len(deduped) == 1
    assert removed == 1


def test_dedup_removes_near_duplicate_titles() -> None:
    a = make_post(id="a", title="How do I configure my eSIM for IoT devices")
    b = make_post(id="b", title="How do I configure my eSIM for IoT device")
    deduped, removed = deduplicate_posts([a, b])
    assert len(deduped) == 1
    assert removed == 1


def test_dedup_keeps_genuinely_different_titles() -> None:
    a = make_post(id="a", title="How do I configure my eSIM")
    b = make_post(id="b", title="What is the best whole life insurance policy")
    deduped, removed = deduplicate_posts([a, b])
    assert len(deduped) == 2
    assert removed == 0


# --- spam filter ---


def test_removed_post_is_spam() -> None:
    assert is_spam(make_post(title="", selftext="[removed]")) is True


def test_low_score_post_is_spam() -> None:
    assert is_spam(make_post(score=-10)) is True


def test_promotional_phrase_is_spam() -> None:
    assert is_spam(make_post(selftext="Check out my new course, DM me for a discount!")) is True


def test_link_stuffed_post_is_spam() -> None:
    text = "https://a.com https://b.com https://c.com"
    assert is_spam(make_post(selftext=text)) is True


def test_all_caps_title_is_spam() -> None:
    assert is_spam(make_post(title="THIS IS THE BEST PRODUCT EVER BUY NOW TODAY")) is True


def test_normal_post_is_not_spam() -> None:
    assert is_spam(make_post(title="Question about IoT connectivity", score=15)) is False


def test_filter_spam_counts_removed() -> None:
    posts = [make_post(id="1", score=15), make_post(id="2", score=-100)]
    kept, removed = filter_spam(posts)
    assert len(kept) == 1
    assert removed == 1


# --- extraction ---


def test_extract_questions_from_title_body_and_comments() -> None:
    post = make_post(
        title="How does eSIM work?",
        selftext="Also, is it more reliable than a physical SIM?",
        top_comments=[make_comment(body="Does it cost extra?")],
    )
    questions = extract_questions(post)
    assert any("How does eSIM work" in q for q in questions)
    assert any("is it more reliable" in q for q in questions)
    assert any("Does it cost extra" in q for q in questions)


def test_extract_pain_points_matches_lexicon() -> None:
    post = make_post(selftext="I'm so frustrated with how unreliable this connection is.")
    pain_points = extract_pain_points(post)
    assert pain_points


def test_extract_pain_points_empty_when_no_match() -> None:
    post = make_post(selftext="Everything is working great, no complaints.")
    assert extract_pain_points(post) == []


def test_detect_buying_signals_matches_lexicon() -> None:
    post = make_post(selftext="I'm in the market for a new IoT connectivity provider.")
    assert detect_buying_signals(post)


def test_detect_competitor_mentions_whole_word_case_insensitive() -> None:
    post = make_post(selftext="We switched away from Emnify last year.")
    mentions = detect_competitor_mentions(post, ["Emnify"])
    assert mentions == ["Emnify"]


def test_detect_competitor_mentions_no_false_positive_substring() -> None:
    post = make_post(selftext="Emnifying is not a real word.")
    # "Emnify" should not match inside "Emnifying" due to word boundary
    assert detect_competitor_mentions(post, ["Emnify"]) == []


# --- orchestrator ---


def test_analyze_posts_end_to_end() -> None:
    relevant = make_post(
        id="r1",
        title="Struggling with IoT connectivity reliability, any recommendations for a provider?",
        selftext="We switched away from Emnify and it's still unreliable. Any advice?",
        score=20,
    )
    spammy = make_post(id="s1", title="BUY NOW CLICK HERE FOR DISCOUNT", score=-50)
    off_topic = make_post(id="o1", title="My cat is cute", score=5)

    analyzed, duplicates_removed, spam_removed = analyze_posts(
        [relevant, spammy, off_topic],
        topic="IoT connectivity",
        keywords=["reliability"],
        competitor_names=["Emnify"],
        min_relevance=0.05,
    )

    assert spam_removed == 1
    assert duplicates_removed == 0
    ids = [a.post.id for a in analyzed]
    assert "r1" in ids
    assert "s1" not in ids

    top = analyzed[0]
    assert top.post.id == "r1"
    assert top.pain_points
    assert top.buying_signals
    assert top.competitor_mentions == ["Emnify"]
