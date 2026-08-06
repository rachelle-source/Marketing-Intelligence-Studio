from pathlib import Path

from backend.config import AppConfig


def test_defaults_are_relative_to_project_root() -> None:
    config = AppConfig(_env_file=None)
    assert config.environment == "development"
    assert config.log_level == "INFO"
    assert config.claude_api_key is None


def test_env_overrides_apply(monkeypatch) -> None:
    monkeypatch.setenv("MIS_CLAUDE_API_KEY", "test-key-123")
    monkeypatch.setenv("MIS_LOG_LEVEL", "DEBUG")
    config = AppConfig(_env_file=None)
    assert config.claude_api_key == "test-key-123"
    assert config.log_level == "DEBUG"


def test_ensure_directories_creates_expected_dirs(tmp_path: Path) -> None:
    config = AppConfig(
        _env_file=None,
        clients_dir=tmp_path / "clients",
        logs_dir=tmp_path / "logs",
        output_dir=tmp_path / "output",
        data_dir=tmp_path / "data",
    )
    config.ensure_directories()
    assert config.clients_dir.is_dir()
    assert config.logs_dir.is_dir()
    assert config.output_dir.is_dir()
    assert config.data_dir.is_dir()
