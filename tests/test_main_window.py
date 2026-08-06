"""Smoke tests for the Tkinter main window.

Skipped automatically wherever there's no display (no X server / no Tk) —
these assert the window can be *built* and *wired up*, not that it looks
right. Run under `xvfb-run` to actually exercise them; that's how they run
in this project's own dev environment.

Run() is threaded (see main_window.py's module docstring for why), so these
tests start it the normal way (`_on_run_click`), join the worker thread
directly instead of waiting on Tk's event loop, then call
`_poll_result_queue()` once to deliver the result — equivalent to what
`after()` would do on the next real tick, just synchronous for testing.
"""

from __future__ import annotations

import pytest

tk = pytest.importorskip("tkinter")

from frontend.client_discovery import ClientSummary  # noqa: E402
from frontend.run_controller import RunController  # noqa: E402
from frontend.tools import list_marketing_tools  # noqa: E402


class FakeRedditService:
    def __init__(self, markdown: str = "## Report\n\nfull markdown here") -> None:
        self._markdown = markdown
        self.calls: list[tuple[str, str]] = []

    def run_and_report(self, client_id: str, topic: str):
        self.calls.append((client_id, topic))
        return (object(), self._markdown)


def _make_window(reddit_service=None):
    from frontend.main_window import MainWindow

    clients = [
        ClientSummary(slug="kore", display_name="KORE Wireless", status="populated"),
        ClientSummary(slug="korr", display_name="korr", status="no_source_data"),
    ]
    tools = list_marketing_tools()
    controller = RunController(reddit_service or FakeRedditService())
    try:
        window = MainWindow(clients=clients, tools=tools, controller=controller)
    except tk.TclError as exc:
        pytest.skip(f"no display available for Tk: {exc}")
    return window


def _run_and_wait(window) -> None:
    """Click Run, wait for the worker thread, then deliver the result the
    way `after()` normally would.
    """
    window._on_run_click()
    assert window._last_thread is not None
    window._last_thread.join(timeout=5)
    window._poll_result_queue()


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
        _run_and_wait(window)
        output = window._output_text.get("1.0", "end").strip()
        assert output  # some guidance message was shown, not a crash
        assert str(window._run_button["state"]) == "normal"  # re-enabled after completion
    finally:
        window.destroy()


def test_successful_run_shows_full_report_and_status() -> None:
    fake_service = FakeRedditService(markdown="## Reddit Research\n\nSome real findings here.")
    window = _make_window(fake_service)
    try:
        reddit_index = next(i for i, t in enumerate(window._tools) if t.key == "reddit_research")
        window._client_listbox.selection_set(0)
        window._tool_listbox.selection_set(reddit_index)
        window._on_tool_selected()
        window._topic_var.set("pricing")

        _run_and_wait(window)

        output = window._output_text.get("1.0", "end")
        assert "Some real findings here." in output
        assert fake_service.calls == [("kore", "pricing")]
        assert "Completed" in window._status_var.get()
    finally:
        window.destroy()


def test_run_button_disabled_while_running() -> None:
    window = _make_window()
    try:
        window._on_run_click()
        # Immediately after the click (before the background thread has been
        # joined/polled), the button should already be disabled.
        assert str(window._run_button["state"]) == "disabled"
        window._last_thread.join(timeout=5)
        window._poll_result_queue()
        assert str(window._run_button["state"]) == "normal"
    finally:
        window.destroy()


def test_enter_key_in_topic_field_triggers_run() -> None:
    fake_service = FakeRedditService()
    window = _make_window(fake_service)
    try:
        reddit_index = next(i for i, t in enumerate(window._tools) if t.key == "reddit_research")
        window._client_listbox.selection_set(0)
        window._tool_listbox.selection_set(reddit_index)
        window._on_tool_selected()
        window._topic_var.set("pricing")

        window.update()
        window._topic_entry.focus_force()
        window.update()
        window._topic_entry.event_generate("<Return>")
        window.update()

        assert window._last_thread is not None
        window._last_thread.join(timeout=5)
        window._poll_result_queue()
        assert fake_service.calls == [("kore", "pricing")]
    finally:
        window.destroy()


def test_double_click_while_running_does_not_start_a_second_thread() -> None:
    window = _make_window()
    try:
        window._on_run_click()
        first_thread = window._last_thread
        window._on_run_click()  # should be ignored — a run is already in flight
        assert window._last_thread is first_thread

        first_thread.join(timeout=5)
        window._poll_result_queue()
    finally:
        window.destroy()
