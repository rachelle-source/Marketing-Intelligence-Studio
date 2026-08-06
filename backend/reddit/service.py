"""RedditService: the PRAW-backed ResearchService implementation.

Version 1 of Reddit research. Per explicit direction, this does not wait on
the never-delivered legacy scraper — it is built directly on PRAW.

Pipeline: load client context -> generate search queries -> fetch posts via
PRAW -> deduplicate -> filter spam -> score relevance -> extract questions /
pain points / buying signals / competitor mentions -> persist a
ResearchSession -> return the full structured report.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from backend.core.database import Database
from backend.models._shared import new_id, utcnow
from backend.models.research import ResearchSession
from backend.reddit.analysis import DEFAULT_MIN_RELEVANCE, analyze_posts
from backend.reddit.client import DEFAULT_COMMENT_LIMIT, DEFAULT_POST_LIMIT, RedditClient
from backend.reddit.client_context import load_client_context
from backend.reddit.models import RedditResearchReport
from backend.reddit.query_builder import build_search_queries
from backend.services.research_service import ResearchService

logger = logging.getLogger(__name__)


class RedditService(ResearchService):
    """Reddit research, backed by PRAW, aware of each client's own intelligence."""

    def __init__(
        self,
        database: Database,
        clients_dir: Path,
        client: RedditClient | None = None,
    ) -> None:
        super().__init__()
        self._db = database
        self._clients_dir = clients_dir
        self._client = client or RedditClient()

    def research(
        self,
        client_id: str,
        topic: str,
        subreddits: Sequence[str] | None = None,
        post_limit: int = DEFAULT_POST_LIMIT,
        comment_limit: int = DEFAULT_COMMENT_LIMIT,
        min_relevance: float = DEFAULT_MIN_RELEVANCE,
    ) -> RedditResearchReport:
        """Run the full research pipeline and return the structured report.

        This is the method the research pipeline should call for the full
        result set (posts, questions, pain points, buying signals,
        competitor mentions). `run_reddit_research` (below) is the thinner
        adapter required by the `ResearchService` interface.
        """
        context = load_client_context(self._clients_dir, client_id)
        queries = build_search_queries(topic, context.primary_keywords)

        self.logger.info(
            "Running Reddit research for client=%s topic=%r using %d generated query/queries",
            client_id,
            topic,
            len(queries),
        )

        all_posts = []
        for query in queries:
            all_posts.extend(
                self._client.search_posts(
                    query,
                    subreddits=subreddits,
                    post_limit=post_limit,
                    comment_limit=comment_limit,
                )
            )

        analyzed, duplicates_removed, spam_removed = analyze_posts(
            all_posts,
            topic=topic,
            keywords=context.primary_keywords,
            competitor_names=context.competitor_names,
            min_relevance=min_relevance,
        )

        report = RedditResearchReport(
            client_id=client_id,
            topic=topic,
            generated_queries=queries,
            subreddits=list(subreddits) if subreddits else ["all"],
            total_fetched=len(all_posts),
            duplicates_removed=duplicates_removed,
            spam_removed=spam_removed,
            analyzed_posts=analyzed,
        )
        self.logger.info(
            "Reddit research complete for client=%s: %d fetched -> %d kept "
            "(%d duplicates, %d spam removed); %d questions, %d pain points, "
            "%d buying signals, %d competitor mentions",
            client_id,
            report.total_fetched,
            len(analyzed),
            duplicates_removed,
            spam_removed,
            report.total_questions,
            report.total_pain_points,
            report.total_buying_signals,
            report.total_competitor_mentions,
        )
        return report

    def run_reddit_research(
        self, client_id: str, query: str, subreddits: Sequence[str] | None = None
    ) -> ResearchSession:
        """`ResearchService`-conforming adapter: run `research`, persist a
        `ResearchSession` summarizing it, and return that session.
        """
        report = self.research(client_id, query, subreddits=subreddits)
        summary = (
            f"{len(report.analyzed_posts)} relevant post(s) found "
            f"({report.total_fetched} fetched, {report.duplicates_removed} duplicates "
            f"and {report.spam_removed} spam/low-quality removed). "
            f"{report.total_questions} question(s), {report.total_pain_points} pain point(s), "
            f"{report.total_buying_signals} buying signal(s), "
            f"{report.total_competitor_mentions} competitor mention(s)."
        )

        session = ResearchSession(
            id=new_id(),
            client_id=client_id,
            project_id=None,
            source_type="reddit",
            query=query,
            summary=summary,
            created_at=utcnow(),
        )
        self._save_session(session)
        self.logger.info("Saved research session %s for client %s", session.id, client_id)
        return session

    def list_sessions(self, client_id: str) -> list[ResearchSession]:
        with self._db.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, client_id, project_id, source_type, query, summary, created_at
                FROM research_sessions
                WHERE client_id = ? AND source_type = 'reddit'
                ORDER BY created_at DESC
                """,
                (client_id,),
            ).fetchall()
        return [
            ResearchSession(
                id=row["id"],
                client_id=row["client_id"],
                project_id=row["project_id"],
                source_type=row["source_type"],
                query=row["query"],
                summary=row["summary"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _save_session(self, session: ResearchSession) -> None:
        """Persist the session, first ensuring a matching `clients` row exists.

        Clients live as files under `clients/<slug>/` (see clients/README.md)
        — there is no `ClientService` syncing them into the database yet, but
        `research_sessions.client_id` has a foreign key against `clients.id`.
        This upserts a minimal row (id = slug) so that FK is satisfied without
        building full client CRUD. See the architecture notes in README.md.
        """
        now = utcnow().isoformat()
        with self._db.connect() as conn:
            conn.execute(
                """
                INSERT INTO clients (id, company, website, industry, products, competitors, created_at, updated_at)
                VALUES (:id, :company, NULL, NULL, '[]', '[]', :now, :now)
                ON CONFLICT(id) DO NOTHING
                """,
                {"id": session.client_id, "company": session.client_id, "now": now},
            )
            conn.execute(
                """
                INSERT INTO research_sessions (id, client_id, project_id, source_type, query, summary, created_at)
                VALUES (:id, :client_id, :project_id, :source_type, :query, :summary, :created_at)
                """,
                {
                    "id": session.id,
                    "client_id": session.client_id,
                    "project_id": session.project_id,
                    "source_type": session.source_type,
                    "query": session.query,
                    "summary": session.summary,
                    "created_at": session.created_at.isoformat(),
                },
            )
