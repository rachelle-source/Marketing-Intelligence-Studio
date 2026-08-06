"""Wires a (client, tool, topic) selection to the real backend service calls.

Kept Tk-free and fully unit-testable on its own — `main_window.py` is the
only module that imports `tkinter`.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from backend.core.errors import AppError
from backend.reddit.service import RedditService
from frontend.client_discovery import ClientSummary
from frontend.tools import ToolDefinition

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    """Outcome of a Run click, ready to display as-is in the UI."""

    success: bool
    message: str
    duration_seconds: float | None = None


class RunController:
    """The one place the UI calls into backend services — never directly."""

    def __init__(self, reddit_service: RedditService) -> None:
        self._reddit_service = reddit_service

    def run(
        self,
        client: ClientSummary | None,
        tool: ToolDefinition | None,
        topic: str = "",
    ) -> RunResult:
        if client is None:
            return RunResult(False, "Select a client first.")
        if tool is None:
            return RunResult(False, "Select a tool first.")
        if not tool.available:
            return RunResult(False, f"{tool.name} is not implemented yet — see {tool.backing_module}.")
        if tool.requires_topic and not topic.strip():
            return RunResult(False, f"{tool.name} needs a topic. Enter one and click Run again.")

        if tool.key == "reddit_research":
            return self._run_reddit_research(client, topic.strip())

        return RunResult(False, f"{tool.name} has no run handler wired up yet.")

    def _run_reddit_research(self, client: ClientSummary, topic: str) -> RunResult:
        logger.info("Running Reddit Research for client=%s topic=%r", client.slug, topic)
        started = time.perf_counter()
        try:
            _session, report_markdown = self._reddit_service.run_and_report(client.slug, topic)
        except AppError as exc:
            elapsed = time.perf_counter() - started
            logger.warning("Reddit research failed for client=%s topic=%r: %s", client.slug, topic, exc)
            return RunResult(False, f"Reddit research failed: {exc.message}", elapsed)
        except Exception as exc:  # noqa: BLE001 - last line of defense before the UI
            elapsed = time.perf_counter() - started
            logger.exception("Unexpected error running Reddit research for client=%s", client.slug)
            return RunResult(False, f"Unexpected error: {exc}", elapsed)

        elapsed = time.perf_counter() - started
        return RunResult(True, report_markdown, elapsed)
