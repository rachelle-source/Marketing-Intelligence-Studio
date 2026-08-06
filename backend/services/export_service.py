"""ExportService interface: generate Markdown, DOCX, HTML, and PDF exports.

TODO: no concrete implementation yet. The Markdown exporter is the first
planned implementation (see project TODOs); DOCX/HTML/PDF follow later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.export import ExportRecord
from backend.services.base import BaseService


class ExportService(BaseService, ABC):
    """Defines the contract for exporting generated content to a file format."""

    @abstractmethod
    def export_markdown(self, content_id: str) -> ExportRecord:
        """Export a content record to Markdown. TODO: Markdown exporter."""

    @abstractmethod
    def export_docx(self, content_id: str) -> ExportRecord:
        """Export a content record to DOCX."""

    @abstractmethod
    def export_html(self, content_id: str) -> ExportRecord:
        """Export a content record to HTML."""

    @abstractmethod
    def export_pdf(self, content_id: str) -> ExportRecord:
        """Export a content record to PDF."""
