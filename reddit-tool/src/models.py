from dataclasses import dataclass, field

@dataclass
class Thread:
    title: str
    body: str
    url: str
    upvotes: int
    created_utc: float
    subreddit: str
    num_comments: int

@dataclass
class ScoredThread:
    thread: Thread
    score: int
    reason: str

@dataclass
class DraftedReply:
    thread: Thread
    draft: str
    lint_score: int = 0
    lint_passed: bool = True
    lint_warnings: list[str] = field(default_factory=list)
    attempts: int = 1

@dataclass
class ClientConfig:
    client_name: str
    subreddits: list[str]
    keywords: list[str]
    brand_context: str
    notify_email: str
    max_threads: int
    sort: str
