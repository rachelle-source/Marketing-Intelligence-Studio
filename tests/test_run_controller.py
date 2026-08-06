from backend.core.errors import ServiceError
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
    def __init__(self, markdown: str | None = None, error: Exception | None = None) -> None:
        self._markdown = markdown
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def run_and_report(self, client_id: str, topic: str):
        self.calls.append((client_id, topic))
        if self._error is not None:
            raise self._error
        return (object(), self._markdown)


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


def test_reddit_research_success_returns_full_report_markdown() -> None:
    fake_service = FakeRedditService(markdown="## Reddit Research — \"pricing\"\n\nfull report here")
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.success is True
    assert "full report here" in result.message
    assert fake_service.calls == [("kore", "pricing")]


def test_reddit_research_reports_duration() -> None:
    fake_service = FakeRedditService(markdown="report")
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.duration_seconds is not None
    assert result.duration_seconds >= 0


def test_reddit_research_structured_error_is_surfaced() -> None:
    fake_service = FakeRedditService(error=ServiceError("boom", details={}))
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.success is False
    assert "boom" in result.message
    assert result.duration_seconds is not None


def test_reddit_research_unexpected_error_does_not_crash() -> None:
    fake_service = FakeRedditService(error=RuntimeError("network blew up"))
    controller = RunController(fake_service)

    result = controller.run(CLIENT, REDDIT_TOOL, "pricing")

    assert result.success is False
    assert "network blew up" in result.message
