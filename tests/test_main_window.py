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

import tempfile
from pathlib import Path

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
        return (object(), self._markdown, Path(f"/tmp/clients/{client_id}/knowledge/reddit.md"))


def _make_window(reddit_service=None, output_dir: Path | None = None):
    from frontend.main_window import MainWindow

    clients = [
        ClientSummary(slug="kore", display_name="KORE Wireless", status="populated"),
        ClientSummary(slug="korr", display_name="korr", status="no_source_data"),
    ]
    tools = list_marketing_tools()
    controller = RunController(reddit_service or FakeRedditService())
    resolved_output_dir = output_dir or Path(tempfile.mkdtemp())
    try:
        window = MainWindow(
            clients=clients, tools=tools, controller=controller, output_dir=resolved_output_dir
        )
        window.update()  # map the window — focus_get()/focus_set() need this under Xvfb
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
    window.update()


def _set_topic(window, text: str) -> None:
    """Set the topic entry's text as if a user had clicked in and typed —
    clears the placeholder deterministically rather than relying on a real
    focus event firing before the next line runs.
    """
    window._on_topic_focus_in(None)
    window._topic_entry.delete(0, "end")
    window._topic_entry.insert(0, text)


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
        _set_topic(window, "pricing")

        _run_and_wait(window)

        output = window._output_text.get("1.0", "end")
        assert "Some real findings here." in output
        assert fake_service.calls == [("kore", "pricing")]
        assert "Completed" in window._status_var.get()
        assert "saved to" in window._status_var.get()
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

        window.update()
        window._topic_entry.focus_force()
        window.update()
        _set_topic(window, "pricing")
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


# --- friction-reduction behaviors ------------------------------------------


def test_reddit_research_is_preselected_on_launch() -> None:
    window = _make_window()
    try:
        tool = window._selected_tool()
        assert tool is not None
        assert tool.key == "reddit_research"
    finally:
        window.destroy()


def test_topic_entry_already_enabled_on_launch() -> None:
    # Because Reddit Research is preselected, the topic field should be
    # usable immediately — no extra click needed to "unlock" it.
    window = _make_window()
    try:
        assert str(window._topic_entry["state"]) == "normal"
    finally:
        window.destroy()


def test_unavailable_tools_are_visually_dimmed() -> None:
    window = _make_window()
    try:
        for index, tool in enumerate(window._tools):
            fg = window._tool_listbox.itemconfig(index)["foreground"][-1]
            if tool.available:
                assert fg == "" or fg == window._topic_default_fg
            else:
                assert fg != ""
    finally:
        window.destroy()


def test_welcome_message_shown_before_any_run() -> None:
    window = _make_window()
    try:
        output = window._output_text.get("1.0", "end")
        assert "Pick a client" in output
        assert "press Enter" in output
    finally:
        window.destroy()


def test_topic_placeholder_shown_and_not_sent_as_real_topic() -> None:
    fake_service = FakeRedditService()
    window = _make_window(fake_service)
    try:
        window._client_listbox.selection_set(0)
        assert window._topic_placeholder_active is True
        assert window._topic_entry.get()  # placeholder text is visible

        _run_and_wait(window)

        # The placeholder must never be treated as a real topic.
        assert fake_service.calls == []
        output = window._output_text.get("1.0", "end")
        assert "needs a topic" in output
    finally:
        window.destroy()


def test_focus_in_clears_placeholder_focus_out_restores_it() -> None:
    window = _make_window()
    try:
        assert window._topic_placeholder_active is True
        window._on_topic_focus_in(None)
        assert window._topic_placeholder_active is False
        assert window._topic_entry.get() == ""

        window._on_topic_focus_out(None)
        assert window._topic_placeholder_active is True
    finally:
        window.destroy()


def test_missing_client_returns_focus_to_client_list() -> None:
    window = _make_window()
    try:
        _set_topic(window, "pricing")
        _run_and_wait(window)
        # focus_get() reports the currently focused widget by its Tk path;
        # comparing identity avoids depending on internal Tk naming.
        assert window.focus_get() is window._client_listbox
    finally:
        window.destroy()


def test_missing_topic_returns_focus_to_topic_entry() -> None:
    window = _make_window()
    try:
        window._client_listbox.selection_set(0)
        _run_and_wait(window)
        assert window.focus_get() is window._topic_entry
    finally:
        window.destroy()


def test_successful_run_selects_topic_text_for_easy_retyping() -> None:
    fake_service = FakeRedditService()
    window = _make_window(fake_service)
    try:
        window._client_listbox.selection_set(0)
        _set_topic(window, "pricing")

        _run_and_wait(window)

        assert window.focus_get() is window._topic_entry
        assert window._topic_entry.selection_present()
    finally:
        window.destroy()


def test_status_bar_uses_plain_language_not_a_fraction() -> None:
    window = _make_window()
    try:
        status = window._status_var.get()
        assert "client(s) ready" in status
        assert "Reddit Research is ready to run" in status
        assert "/4" not in status
    finally:
        window.destroy()


def test_initial_focus_is_on_client_list() -> None:
    window = _make_window()
    try:
        assert window.focus_get() is window._client_listbox
    finally:
        window.destroy()


# --- export buttons (Save for NotebookLM / Open Export Folder / Copy Report) ---


def test_export_buttons_disabled_before_any_run() -> None:
    window = _make_window()
    try:
        assert str(window._save_button["state"]) == "disabled"
        assert str(window._open_folder_button["state"]) == "disabled"
        assert str(window._copy_button["state"]) == "disabled"
    finally:
        window.destroy()


def test_export_buttons_enabled_after_successful_run(tmp_path: Path) -> None:
    window = _make_window(output_dir=tmp_path)
    try:
        window._client_listbox.selection_set(0)
        _set_topic(window, "pricing")
        _run_and_wait(window)

        assert str(window._save_button["state"]) == "normal"
        assert str(window._open_folder_button["state"]) == "normal"
        assert str(window._copy_button["state"]) == "normal"
    finally:
        window.destroy()


def test_export_buttons_disabled_again_after_a_failed_run(tmp_path: Path) -> None:
    window = _make_window(output_dir=tmp_path)
    try:
        window._client_listbox.selection_set(0)
        _set_topic(window, "pricing")
        _run_and_wait(window)
        assert str(window._save_button["state"]) == "normal"

        # A second run with no client selected should disable them again.
        window._client_listbox.selection_clear(0, "end")
        _run_and_wait(window)

        assert str(window._save_button["state"]) == "disabled"
        assert str(window._open_folder_button["state"]) == "disabled"
        assert str(window._copy_button["state"]) == "disabled"
    finally:
        window.destroy()


def test_save_for_notebooklm_writes_a_file(tmp_path: Path) -> None:
    fake_service = FakeRedditService(markdown="## Reddit Research Brief — \"pricing\"\n\nfindings")
    window = _make_window(fake_service, output_dir=tmp_path)
    try:
        window._client_listbox.selection_set(0)
        _set_topic(window, "pricing")
        _run_and_wait(window)

        window._on_save_for_notebooklm_click()

        files = list((tmp_path / "kore").glob("*.md"))
        assert len(files) == 1
        assert "pricing" in files[0].name
        content = files[0].read_text(encoding="utf-8")
        assert content.startswith("# Reddit Research Brief")
        assert "findings" in content
        assert "Saved for NotebookLM" in window._status_var.get()
    finally:
        window.destroy()


def test_open_export_folder_calls_the_os_helper(tmp_path: Path, monkeypatch) -> None:
    import frontend.main_window as main_window_module

    calls = []
    monkeypatch.setattr(main_window_module, "open_in_file_manager", lambda p: calls.append(p))

    window = _make_window(output_dir=tmp_path)
    try:
        window._client_listbox.selection_set(0)
        _set_topic(window, "pricing")
        _run_and_wait(window)

        window._on_open_export_folder_click()

        assert calls == [tmp_path / "kore"]
        assert "Opened kore/" in window._status_var.get()
    finally:
        window.destroy()


def test_copy_report_puts_markdown_on_clipboard(tmp_path: Path) -> None:
    fake_service = FakeRedditService(markdown="## Report\n\nsome findings to copy")
    window = _make_window(fake_service, output_dir=tmp_path)
    try:
        window._client_listbox.selection_set(0)
        _set_topic(window, "pricing")
        _run_and_wait(window)

        window._on_copy_report_click()
        window.update()

        assert window.clipboard_get() == "## Report\n\nsome findings to copy"
        assert "copied to clipboard" in window._status_var.get()
    finally:
        window.destroy()


def test_export_buttons_do_nothing_before_a_client_is_picked() -> None:
    # Defensive: clicking them with no last-run state must not raise.
    window = _make_window()
    try:
        window._on_save_for_notebooklm_click()
        window._on_open_export_folder_click()
        window._on_copy_report_click()
    finally:
        window.destroy()
