from frontend.tools import list_marketing_tools


def test_returns_nonempty_list() -> None:
    assert list_marketing_tools()


def test_reddit_research_is_available_and_needs_a_topic() -> None:
    tools = {t.key: t for t in list_marketing_tools()}
    reddit_tool = tools["reddit_research"]
    assert reddit_tool.available is True
    assert reddit_tool.requires_topic is True
    assert reddit_tool.backing_module == "backend.reddit.RedditService"


def test_other_tools_are_not_yet_available() -> None:
    tools = {t.key: t for t in list_marketing_tools()}
    for key in ("ai_writer", "knowledge_extraction", "markdown_export"):
        assert tools[key].available is False


def test_every_tool_has_a_backing_module_reference() -> None:
    for tool in list_marketing_tools():
        assert tool.backing_module
