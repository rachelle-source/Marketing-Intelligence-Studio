from pathlib import Path

from frontend import os_actions


def test_creates_directory_if_missing(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "does" / "not" / "exist"
    monkeypatch.setattr(os_actions.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(os_actions.platform, "system", lambda: "Linux")

    os_actions.open_in_file_manager(target)

    assert target.is_dir()


def test_uses_xdg_open_on_linux(tmp_path: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(os_actions.subprocess, "run", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(os_actions.platform, "system", lambda: "Linux")

    os_actions.open_in_file_manager(tmp_path)

    assert calls == [(["xdg-open", str(tmp_path)],)]


def test_uses_open_on_macos(tmp_path: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(os_actions.subprocess, "run", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(os_actions.platform, "system", lambda: "Darwin")

    os_actions.open_in_file_manager(tmp_path)

    assert calls == [(["open", str(tmp_path)],)]


def test_uses_startfile_on_windows(tmp_path: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(os_actions.platform, "system", lambda: "Windows")
    monkeypatch.setattr(os_actions.os, "startfile", lambda p: calls.append(p), raising=False)

    os_actions.open_in_file_manager(tmp_path)

    assert calls == [str(tmp_path)]


def test_does_not_raise_when_opener_fails(tmp_path: Path, monkeypatch) -> None:
    def boom(*_a, **_k):
        raise OSError("no file manager available")

    monkeypatch.setattr(os_actions.subprocess, "run", boom)
    monkeypatch.setattr(os_actions.platform, "system", lambda: "Linux")

    os_actions.open_in_file_manager(tmp_path)  # must not raise
