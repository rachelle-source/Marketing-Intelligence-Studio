"""Tests for backend.config._detect_base_dir — the logic that decides where
a packaged (PyInstaller-frozen) build looks for .env / data / logs / output,
since it must NOT be the bundle-internal temp/resources path.
"""

from pathlib import Path

from backend.config import _detect_base_dir


def test_not_frozen_resolves_to_repo_root(monkeypatch) -> None:
    monkeypatch.delattr("sys.frozen", raising=False)
    base = _detect_base_dir()
    assert (base / "backend").is_dir()
    assert (base / "frontend").is_dir()


def test_frozen_windows_style_resolves_next_to_executable(monkeypatch) -> None:
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr(
        "sys.executable", "/Users/marketer/Desktop/App/MarketingIntelligenceStudio.exe"
    )
    base = _detect_base_dir()
    assert base == Path("/Users/marketer/Desktop/App")


def test_frozen_macos_app_bundle_resolves_next_to_dot_app(monkeypatch) -> None:
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr(
        "sys.executable",
        "/Users/marketer/Desktop/Marketing Intelligence Studio.app/Contents/MacOS/MarketingIntelligenceStudio",
    )
    base = _detect_base_dir()
    assert base == Path("/Users/marketer/Desktop")


def test_frozen_onedir_without_contents_folder_uses_direct_parent(monkeypatch) -> None:
    # A Windows onedir build has no "Contents" ancestor at all — must not
    # mistakenly take the macOS branch. (Using a POSIX-style path here since
    # pathlib.Path on this test runner is PosixPath either way — the point is
    # the "no Contents ancestor" branch, not actual Windows drive-letter
    # semantics, which only a WindowsPath on real Windows would exercise.)
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", "/opt/mis/MarketingIntelligenceStudio.exe")
    base = _detect_base_dir()
    assert base == Path("/opt/mis")
