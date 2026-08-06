"""Tests for the Reddit credential setup dialog and its wiring.

Covers: the plain functions (`credentials_present`, `save_reddit_credentials`)
with no Tk dependency, the dialog itself under Xvfb, and its integration
points in `MainWindow` / `RunController` — the first-run "no .env editing
required" flow described in README.md's Packaging & distribution section.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

import frontend.credential_setup as credential_setup  # noqa: E402
from frontend.credential_setup import (  # noqa: E402
    RedditSetupDialog,
    credentials_present,
    save_reddit_credentials,
)
from frontend.run_controller import RunController, RunResult  # noqa: E402


# --- credentials_present() --------------------------------------------------


def test_credentials_present_false_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    assert credentials_present() is False


def test_credentials_present_false_when_only_one_set(monkeypatch) -> None:
    monkeypatch.setenv("REDDIT_CLIENT_ID", "abc")
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    assert credentials_present() is False


def test_credentials_present_true_when_both_set(monkeypatch) -> None:
    monkeypatch.setenv("REDDIT_CLIENT_ID", "abc")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "xyz")
    assert credentials_present() is True


# --- save_reddit_credentials() ----------------------------------------------


def test_save_reddit_credentials_writes_new_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)

    save_reddit_credentials("my-client-id", "my-secret")

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "REDDIT_CLIENT_ID=my-client-id" in env_text
    assert "REDDIT_CLIENT_SECRET=my-secret" in env_text
    assert credentials_present() is True


def test_save_reddit_credentials_preserves_other_lines(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".env").write_text(
        "MIS_ENVIRONMENT=production\nREDDIT_USER_AGENT=my-agent\n", encoding="utf-8"
    )
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)

    save_reddit_credentials("new-id", "new-secret")

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "MIS_ENVIRONMENT=production" in env_text
    assert "REDDIT_USER_AGENT=my-agent" in env_text
    assert "REDDIT_CLIENT_ID=new-id" in env_text


def test_save_reddit_credentials_overwrites_not_duplicates(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / ".env").write_text(
        "REDDIT_CLIENT_ID=old-id\nREDDIT_CLIENT_SECRET=old-secret\n", encoding="utf-8"
    )
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)

    save_reddit_credentials("new-id", "new-secret")

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert env_text.count("REDDIT_CLIENT_ID=") == 1
    assert env_text.count("REDDIT_CLIENT_SECRET=") == 1
    assert "old-id" not in env_text
    assert "new-id" in env_text


# --- RedditSetupDialog (GUI) -------------------------------------------------


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError as exc:
        pytest.skip(f"no display available for Tk: {exc}")
    return root


def test_dialog_save_requires_both_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)
    root = _make_root()
    try:
        saved = []
        dialog = RedditSetupDialog(root, on_saved=lambda: saved.append(True))
        dialog._on_save()  # both fields empty
        assert saved == []
        assert dialog.winfo_exists()  # dialog stays open on validation failure
        assert "required" in dialog._error_var.get().lower()
    finally:
        root.destroy()


def test_dialog_save_writes_credentials_and_calls_on_saved(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    root = _make_root()
    try:
        saved = []
        dialog = RedditSetupDialog(root, on_saved=lambda: saved.append(True))
        dialog._client_id_entry.insert(0, "abc123")
        dialog._secret_entry.insert(0, "shh-secret")
        dialog._on_save()

        assert saved == [True]
        assert credentials_present() is True
        assert not dialog.winfo_exists()  # dialog closes itself after saving
    finally:
        root.destroy()


def test_dialog_skip_closes_without_saving(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    root = _make_root()
    try:
        dialog = RedditSetupDialog(root)
        dialog._on_skip()

        assert not dialog.winfo_exists()
        assert not (tmp_path / ".env").exists()
    finally:
        root.destroy()


def test_show_secret_checkbox_toggles_masking(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(credential_setup, "PROJECT_ROOT", tmp_path)
    root = _make_root()
    try:
        dialog = RedditSetupDialog(root)
        assert dialog._secret_entry.cget("show") == "*"
        dialog._show_secret.set(True)
        dialog._toggle_secret_visibility()
        assert dialog._secret_entry.cget("show") == ""
    finally:
        root.destroy()


# --- MainWindow integration ---------------------------------------------------


def _make_window(check_credentials: bool, reddit_service=None, output_dir: Path | None = None):
    from frontend.client_discovery import ClientSummary
    from frontend.main_window import MainWindow
    from frontend.tools import list_marketing_tools

    clients = [ClientSummary(slug="kore", display_name="KORE Wireless", status="populated")]
    controller = RunController(reddit_service)
    resolved_output_dir = output_dir or Path(tempfile.mkdtemp())
    try:
        window = MainWindow(
            clients=clients,
            tools=list_marketing_tools(),
            controller=controller,
            output_dir=resolved_output_dir,
            check_credentials=check_credentials,
        )
        window.update()
    except tk.TclError as exc:
        pytest.skip(f"no display available for Tk: {exc}")
    return window


def test_setup_dialog_opens_on_launch_when_credentials_missing(monkeypatch) -> None:
    monkeypatch.setattr("frontend.main_window.credentials_present", lambda: False)
    opened = []
    monkeypatch.setattr(
        "frontend.main_window.RedditSetupDialog",
        lambda parent, on_saved=None: opened.append(parent),
    )

    window = _make_window(check_credentials=True)
    try:
        assert opened == [window]
    finally:
        window.destroy()


def test_setup_dialog_does_not_open_when_credentials_present(monkeypatch) -> None:
    monkeypatch.setattr("frontend.main_window.credentials_present", lambda: True)
    opened = []
    monkeypatch.setattr(
        "frontend.main_window.RedditSetupDialog",
        lambda parent, on_saved=None: opened.append(parent),
    )

    window = _make_window(check_credentials=True)
    try:
        assert opened == []
    finally:
        window.destroy()


class _CredentialsMissingService:
    def run_and_report(self, client_slug: str, topic: str):
        from backend.reddit.errors import RedditCredentialsError

        raise RedditCredentialsError("Missing Reddit API credentials")


def test_failed_run_due_to_missing_credentials_reopens_setup_dialog(monkeypatch) -> None:
    opened = []
    monkeypatch.setattr(
        "frontend.main_window.RedditSetupDialog",
        lambda parent, on_saved=None: opened.append(parent),
    )

    window = _make_window(check_credentials=False, reddit_service=_CredentialsMissingService())
    try:
        window._client_listbox.selection_set(0)
        window._topic_entry.delete(0, "end")
        window._topic_entry.insert(0, "pricing")
        window._topic_placeholder_active = False

        window._on_run_click()
        window._last_thread.join(timeout=5)
        window._poll_result_queue()

        assert opened == [window]
        assert "isn't connected" in window._output_text.get("1.0", "end")
    finally:
        window.destroy()


def test_run_controller_flags_credentials_missing() -> None:
    controller = RunController(_CredentialsMissingService())
    from frontend.client_discovery import ClientSummary
    from frontend.tools import list_marketing_tools

    client = ClientSummary(slug="kore", display_name="KORE Wireless", status="populated")
    tool = next(t for t in list_marketing_tools() if t.key == "reddit_research")

    result = controller.run(client, tool, "pricing")

    assert isinstance(result, RunResult)
    assert result.success is False
    assert result.credentials_missing is True
