"""Smoke tests for the Tkinter main window.

Skipped automatically wherever there's no display (no X server / no Tk) —
these assert the window can be *built*, not that it looks right. Run under
`xvfb-run` to actually exercise them; that's how they run in this project's
own dev environment.
"""

from __future__ import annotations

import pytest

tk = pytest.importorskip("tkinter")

from frontend.client_discovery import ClientSummary  # noqa: E402
from frontend.run_controller import RunController  # noqa: E402
from frontend.tools import list_marketing_tools  # noqa: E402


def _make_window(monkeypatch=None):
    from frontend.main_window import MainWindow

    clients = [
        ClientSummary(slug="kore", display_name="KORE Wireless", status="populated"),
        ClientSummary(slug="korr", display_name="korr", status="no_source_data"),
    ]
    tools = list_marketing_tools()

    class FakeRedditService:
        def run_reddit_research(self, client_id, query):  # noqa: ARG002
            raise AssertionError("should not be called in this smoke test")

    controller = RunController(FakeRedditService())
    try:
        window = MainWindow(clients=clients, tools=tools, controller=controller)
    except tk.TclError as exc:
        pytest.skip(f"no display available for Tk: {exc}")
    return window


def test_main_window_builds_and_populates_lists() -> None:
    window = _make_window()
    try:
        assert window._client_listbox.size() == 2
        assert window._tool_listbox.size() == len(list_marketing_tools())
        assert "KORE Wireless" in window._client_listbox.get(0)
    finally:
        window.destroy()


def test_selecting_reddit_research_enables_topic_entry() -> None:
    window = _make_window()
    try:
        reddit_index = next(
            i for i, t in enumerate(window._tools) if t.key == "reddit_research"
        )
        window._tool_listbox.selection_clear(0, "end")
        window._tool_listbox.selection_set(reddit_index)
        window._on_tool_selected()
        assert str(window._topic_entry["state"]) == "normal"
    finally:
        window.destroy()


def test_run_without_selection_shows_message_without_crashing() -> None:
    window = _make_window()
    try:
        window._on_run_click()
        output = window._output_text.get("1.0", "end").strip()
        assert output  # some guidance message was shown, not a crash
    finally:
        window.destroy()
