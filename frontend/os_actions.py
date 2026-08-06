"""Small OS-integration helpers — not business logic, just "open this in the
native file manager" so `main_window.py` doesn't need `subprocess`/`os`
sprinkled through its widget code. Kept in its own module so it's mockable
in tests without a real desktop environment.
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def open_in_file_manager(path: Path) -> None:
    """Open ``path`` (creating it first if missing) in the OS file manager."""
    path.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError:
        logger.exception("Could not open %s in the file manager", path)
