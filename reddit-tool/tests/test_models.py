from src.models import Thread, ScoredThread, DraftedReply, ClientConfig

def test_thread_fields():
    t = Thread(
        title="Best solar panels for home?",
        body="Looking for recommendations",
        url="https://reddit.com/r/solar/comments/abc",
        upvotes=42,
        created_utc=1712000000.0,
        subreddit="solar",
        num_comments=12,
    )
    assert t.title == "Best solar panels for home?"
    assert t.subreddit == "solar"

def test_scored_thread_fields():
    t = Thread("t", "b", "u", 1, 1.0, "solar", 1)
    s = ScoredThread(thread=t, score=8, reason="Asking for product recommendation")
    assert s.score == 8

def test_drafted_reply_fields():
    t = Thread("t", "b", "u", 1, 1.0, "solar", 1)
    d = DraftedReply(thread=t, draft="Great question! Consider...")
    assert d.draft.startswith("Great")

def test_client_config_fields():
    c = ClientConfig(
        client_name="ADM Solar",
        subreddits=["solar", "solarenergy"],
        keywords=["solar panels", "solar cost"],
        brand_context="ADM Solar installs residential solar.",
        notify_email="rachelle@keystone.com",
        max_threads=15,
        sort="hot",
    )
    assert c.client_name == "ADM Solar"
    assert len(c.subreddits) == 2
