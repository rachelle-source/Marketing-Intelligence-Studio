"""Export a rendered Reddit Research report to a standalone Markdown file.

Distinct from `report.save_report_to_knowledge_base`: that function
accumulates every run into one running log per client
(`clients/<slug>/knowledge/reddit.md`). This module writes ONE clean,
standalone file per client/topic/day into `output/<slug>/`, named so it
sorts chronologically and reads clearly in a file picker — meant to be
dragged straight into NotebookLM (or anywhere else) as a source document.

Not wired through `backend.services.export_service.ExportService`: that
interface's `export_markdown(content_id)` is shaped for AI Writer content
(blog posts, social copy), not research reports — forcing this into it
would mean inventing a `Content` record for something that isn't one.
"""

from __future__ import annotations

import logging
import re
from datetime import date as date_cls
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_SLUG_LENGTH = 60
_SLUG_INVALID_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Turn a topic into a filename-safe slug: lowercase, hyphenated, capped length."""
    slug = _SLUG_INVALID_RE.sub("-", text.lower()).strip("-")
    slug = slug[:MAX_SLUG_LENGTH].rstrip("-")
    return slug or "topic"


def build_export_filename(topic: str, on: date_cls) -> str:
    """Build the consistent '<date>_<topic-slug>.md' filename for an export."""
    return f"{on.isoformat()}_{slugify(topic)}.md"


def _promote_title(markdown: str) -> str:
    """Promote the report's leading '## ' heading to '# ' for a standalone file.

    Inside the accumulating knowledge base, each run is one section (H2)
    under that file's own title. As its own file, the report should read as
    a document with its own top-level title.
    """
    lines = markdown.split("\n", 1)
    if lines and lines[0].startswith("## "):
        lines[0] = "# " + lines[0][3:]
    return "\n".join(lines)


def export_report_markdown(
    output_dir: Path,
    client_id: str,
    topic: str,
    report_markdown: str,
    on: date_cls | None = None,
) -> Path:
    """Write ``report_markdown`` to ``output_dir/client_id/<date>_<topic>.md``.

    Overwrites any existing export for the same client/topic/day — this is
    a clean snapshot meant for handing off to NotebookLM, not a history
    (the client's ``knowledge/reddit.md`` is the accumulating history).
    """
    client_dir = output_dir / client_id
    client_dir.mkdir(parents=True, exist_ok=True)

    filename = build_export_filename(topic, on or datetime.now().date())
    path = client_dir / filename
    path.write_text(_promote_title(report_markdown), encoding="utf-8")
    logger.info("Exported report for client=%s to %s", client_id, path)
    return path
