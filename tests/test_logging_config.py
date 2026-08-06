import logging
from pathlib import Path

from backend.core.logging_config import configure_logging


def test_configure_logging_creates_log_file(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    configure_logging(logs_dir, level="INFO")

    logger = logging.getLogger("test_logging_config")
    logger.info("hello from test")
    for handler in logging.getLogger().handlers:
        handler.flush()

    log_file = logs_dir / "app.log"
    assert log_file.exists()
    assert "hello from test" in log_file.read_text(encoding="utf-8")
