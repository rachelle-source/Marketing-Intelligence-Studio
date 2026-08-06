from backend.core.errors import ServiceError
from backend.models.research import ResearchSession
from frontend.client_discovery import ClientSummary
from frontend.run_controller import RunController
from frontend.tools import ToolDefinition

CLIENT = ClientSummary(slug="kore", display_name="KORE Wireless", status="populated")

REDDIT_TOOL = ToolDefinition(
    key="reddit_research",
    name="Reddit Research",
    description="...",
    available=True,
    backing_module="backend.reddit.RedditService",
    requires_topic=True,
)

UNAVAILABLE_TOOL = ToolDefinition(
    key="ai_writer",
    name="AI Writer",
    description="...",
    available=False,
    backing_module="backend.services.ai_service.AIService",
)


class FakeRedditService:
    def __init__(self, session=None, error: Exception | None = None) -> None:
        self._session = session
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def run_reddit_research(self, client_id: str, query: str):
        self.calls.append((client_id, query))
        if self._error is not None:
            raise self._error
        return self._session


def make_session(summary: str = "3 relevant post(s) found.") -> ResearchSession:
    return ResearchSession(
        id="s1",
        client_id="kore",
        project_id=None,
        source_type="reddit",
        query="pricing",
        summary=summary,
    )


def test_no_client_selected() -> None:
    controller = RunController(FakeRedditService())
    result = controller.run(None, REDDIT_TOOL, "pricing")
    assert result.success is False
    assert "client" in result.message.lower()


def test_no_tool_selected() -> None:
    controller = RunController(FakeRedditService())
    result = controller.run(CLIENT, None, "pricing")
    assert result.success is False
    assert "tool" in result.message.lower()


def test_unavailable_tool_reports_not_implemented() -> None:
    controller = RunController(FakeRedditService())
    result = controller.run(CLIENT, UNAVAILABLE_TOOL, "")
    assert result.success is False
    assert "not implemented" in result.message.lower()
    assert "AIService" in result.message


def test_reddit_research_without_topic_asks_for_one() -> None:
    controller = RunController(FakeRedditService())
    result = controller.run(CLIENT, REDDIT_TOOL, "  ")
    assert result.success is False
    assert "topic" in result.message.lower()


def test_reddit_research_success_returns_session_summary() -> None:
    fake_service = FakeRedditService(session=make_session("5 relevant post(s) found."))
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.success is True
    assert result.message == "5 relevant post(s) found."
    assert fake_service.calls == [("kore", "pricing")]


def test_reddit_research_structured_error_is_surfaced() -> None:
    fake_service = FakeRedditService(error=ServiceError("boom", details={}))
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.success is False
    assert "boom" in result.message


def test_reddit_research_unexpected_error_does_not_crash() -> None:
    fake_service = FakeRedditService(error=RuntimeError("network blew up"))
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.success is False
    assert "network blew up" in result.message
