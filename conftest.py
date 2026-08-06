"""Ensures the repo root is importable as `backend.*` when running pytest."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: hits a real external service (e.g. live Reddit API); "
        "requires real credentials and is skipped otherwise",
    )
