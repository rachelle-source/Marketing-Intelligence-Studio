"""RedditService: the PRAW-backed ResearchService implementation.

Version 1 of Reddit research. Per explicit direction, this does not wait on
the never-delivered legacy scraper — it is built directly on PRAW.

Pipeline for `research()`:

1. Load client context (SEO keywords, competitor names, display name).
2. Generate a few keyword-paired search queries from the topic.
3. Search Reddit for each query (posts only — no comments yet, for speed).
   A single failing query is logged and skipped rather than aborting the
   whole run; the run only fails if every query fails.
4. Deduplicate, filter spam, score relevance, and keep only the top
   `max_results` posts — ranking never needs comments, only title/selftext.
5. Fetch comments for just those surviving posts (the expensive step,
   deferred until the list is already short).
6. Extract questions / pain points / buying signals / competitor mentions.
7. Return the structured report. `run_and_report` additionally renders it to
   Markdown, saves it into the client's knowledge base, and persists a
   `ResearchSession` row.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from backend.core.database import Database
from backend.models._shared import new_id, utcnow
from backend.models.research import ResearchSession
from backend.reddit.analysis import DEFAULT_MIN_RELEVANCE, build_analyzed_post, select_top_posts
from backend.reddit.client import DEFAULT_COMMENT_LIMIT, DEFAULT_POST_LIMIT, RedditClient
from backend.reddit.client_context import load_client_context
from backend.reddit.errors import RedditSearchError
from backend.reddit.models import RedditPost, RedditResearchReport
from backend.reddit.query_builder import build_search_queries
from backend.reddit.report import render_markdown_report, save_report_to_knowledge_base
from backend.services.research_service import ResearchService

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 10


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
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> RedditResearchReport:
        """Run the full research pipeline and return the structured report."""
        context = load_client_context(self._clients_dir, client_id)
        queries = build_search_queries(topic, context.primary_keywords)

        self.logger.info(
            "Running Reddit research for client=%s topic=%r using %d generated query/queries",
            client_id,
            topic,
            len(queries),
        )

        all_posts, failed_queries = self._search_all_queries(queries, subreddits, post_limit)
        if not all_posts and failed_queries and len(failed_queries) == len(queries):
            raise RedditSearchError(
                f"All {len(queries)} search quer{'y' if len(queries) == 1 else 'ies'} failed",
                details={"queries": queries, "client_id": client_id},
            )

        scored, duplicates_removed, spam_removed = select_top_posts(
            all_posts, topic, context.primary_keywords, min_relevance, max_results
        )
        analyzed = [
            build_analyzed_post(
                self._with_comments(post, comment_limit), relevance, context.competitor_names
            )
            for post, relevance in scored
        ]

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
            "(%d duplicates, %d spam removed, %d query failure(s)); %d questions, "
            "%d pain points, %d buying signals, %d competitor mentions",
            client_id,
            report.total_fetched,
            len(analyzed),
            duplicates_removed,
            spam_removed,
            len(failed_queries),
            report.total_questions,
            report.total_pain_points,
            report.total_buying_signals,
            report.total_competitor_mentions,
        )
        return report

    def _search_all_queries(
        self,
        queries: list[str],
        subreddits: Sequence[str] | None,
        post_limit: int,
    ) -> tuple[list[RedditPost], list[str]]:
        """Search every query, isolating failures so one bad query doesn't
        sink the whole run. Returns (all_posts, failed_queries).
        """
        all_posts: list[RedditPost] = []
        failed_queries: list[str] = []
        for query in queries:
            try:
                all_posts.extend(
                    self._client.search_posts(query, subreddits=subreddits, post_limit=post_limit)
                )
            except RedditSearchError as exc:
                self.logger.warning(
                    "Search query %r failed, continuing with remaining queries: %s", query, exc
                )
                failed_queries.append(query)
        return all_posts, failed_queries

    def _with_comments(self, post: RedditPost, comment_limit: int) -> RedditPost:
        """Fetch and attach top comments for one post. Never raises — a
        failed comment fetch just leaves the post with no comments.
        """
        comments = self._client.fetch_top_comments(post.id, comment_limit)
        if not comments:
            return post
        return post.model_copy(update={"top_comments": comments})

    def run_and_report(
        self, client_id: str, topic: str, subreddits: Sequence[str] | None = None
    ) -> tuple[ResearchSession, str]:
        """Run research, render + save the Markdown report, and persist a
        session. This is what the GUI (and any future caller wanting the
        full report, not just a one-line summary) should call.
        """
        report = self.research(client_id, topic, subreddits=subreddits)
        context = load_client_context(self._clients_dir, client_id)

        report_markdown = render_markdown_report(report, context.display_name)
        save_report_to_knowledge_base(self._clients_dir, client_id, report_markdown)

        summary = (
            f"{len(report.analyzed_posts)} relevant post(s) found "
            f"({report.total_fetched} fetched, {report.duplicates_removed} duplicates "
            f"and {report.spam_removed} spam/low-quality removed). "
            f"{report.total_questions} question(s), {report.total_pain_points} pain point(s), "
            f"{report.total_buying_signals} buying signal(s), "
            f"{report.total_competitor_mentions} competitor mention(s). "
            "Full report saved to the client's knowledge base."
        )
        session = ResearchSession(
            id=new_id(),
            client_id=client_id,
            project_id=None,
            source_type="reddit",
            query=topic,
            summary=summary,
            created_at=utcnow(),
        )
        self._save_session(session)
        self.logger.info("Saved research session %s for client %s", session.id, client_id)
        return session, report_markdown

    def run_reddit_research(
        self, client_id: str, query: str, subreddits: Sequence[str] | None = None
    ) -> ResearchSession:
        """`ResearchService`-conforming adapter — see `run_and_report` for
        the richer result (session + full Markdown report) real callers want.
        """
        session, _ = self.run_and_report(client_id, query, subreddits=subreddits)
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
