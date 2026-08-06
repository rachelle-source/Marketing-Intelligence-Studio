"""Ensures the repo root is importable as `backend.*` when running pytest."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
