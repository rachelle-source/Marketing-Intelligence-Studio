"""Registry of marketing tools shown in the desktop UI.

Each tool maps to a backend service. Unavailable tools stay listed (not
hidden) so the team can see the product roadmap — the Run button explains
plainly why an unavailable tool can't run yet, rather than pretending it
doesn't exist.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    """A marketing tool as shown in the tool list."""

    key: str
    name: str
    description: str
    available: bool
    backing_module: str
    requires_topic: bool = False


def list_marketing_tools() -> list[ToolDefinition]:
    """Return the fixed set of marketing tools this version knows about."""
    return [
        ToolDefinition(
            key="reddit_research",
            name="Reddit Research",
            description=(
                "Search Reddit for a topic, filter out spam/duplicates, and extract "
                "customer questions, pain points, buying signals, and competitor mentions."
            ),
            available=True,
            backing_module="backend.reddit.RedditService",
            requires_topic=True,
        ),
        ToolDefinition(
            key="ai_writer",
            name="AI Writer",
            description="Generate on-brand blog posts, social copy, emails, FAQs, and ad copy.",
            available=False,
            backing_module="backend.services.ai_service.AIService",
        ),
        ToolDefinition(
            key="knowledge_extraction",
            name="Knowledge Extraction",
            description="Extract reusable insights from research sessions into the knowledge base.",
            available=False,
            backing_module="backend.services.knowledge_service.KnowledgeService",
        ),
        ToolDefinition(
            key="markdown_export",
            name="Markdown Export",
            description="Export generated content to a Markdown file.",
            available=False,
            backing_module="backend.services.export_service.ExportService",
        ),
    ]
