from backend.reddit.query_builder import build_search_queries


def test_bare_topic_is_always_first() -> None:
    queries = build_search_queries("pricing", ["IoT connectivity"])
    assert queries[0] == "pricing"


def test_pairs_topic_with_keywords() -> None:
    queries = build_search_queries("pricing", ["IoT connectivity", "enterprise IoT"])
    assert "pricing IoT connectivity" in queries
    assert "pricing enterprise IoT" in queries


def test_respects_max_queries() -> None:
    keywords = [f"keyword{i}" for i in range(10)]
    queries = build_search_queries("topic", keywords, max_queries=3)
    assert len(queries) == 3


def test_no_keywords_returns_bare_topic_only() -> None:
    assert build_search_queries("topic", []) == ["topic"]


def test_deduplicates_case_insensitively() -> None:
    queries = build_search_queries("Topic", ["Topic"])
    lowered = [q.lower() for q in queries]
    assert len(lowered) == len(set(lowered))
