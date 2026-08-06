# UI Guidelines

## Purpose
Provide a consistent, modern desktop experience.

## Design Principles
- Desktop-first
- Clean, minimal interface
- Dark mode first, light mode supported
- Fast and uncluttered
- Client context always visible

## Layout
- Left navigation
- Top toolbar
- Main workspace
- Right context panel (future)
- Bottom status bar

## Primary Navigation
- Dashboard
- Clients
- Research
- AI Writer
- Knowledge
- Exports
- Settings

## Colors
Primary: Navy
Accent: Teal
Success: Green
Warning: Amber
Error: Red

## Typography
- Headings: Inter
- Body: Inter
- Monospace: JetBrains Mono

## UX Rules
- Never hide progress during AI tasks.
- Allow users to cancel long-running operations.
- Every AI response must be editable.
- Remember the last selected client.


# Features

## MVP Features

### Dashboard
Recent activity, quick actions, recent projects.

### Client Manager
Manage client profiles, brand voice, competitors, keywords, prompts.

### Reddit Research
Search Reddit, summarize discussions, extract questions, objections, trends.

### AI Writer
Generate:
- Blogs
- LinkedIn posts
- Reddit replies
- Email drafts
- FAQs
- Ad copy

### Knowledge Base
Store reusable research and insights.

### Export Center
Export to Markdown, DOCX, HTML, and PDF.

### Settings
Theme, AI model, API keys, export preferences.

## Future Features
- Google News
- RSS
- YouTube research
- Team collaboration
- Plugins


# Internal API

## Purpose
Define internal services. This is not a public web API.

## Services

### ClientService
Create, update, load, and delete clients.

### ResearchService
Execute research workflows and collect sources.

### AIService
Build prompts, call Claude, validate responses.

### KnowledgeService
Extract and store reusable insights.

### ExportService
Generate Markdown, DOCX, HTML, and PDF.

### SettingsService
Manage application configuration.

## Rules
- UI never calls external APIs directly.
- All AI requests go through AIService.
- Services communicate through well-defined interfaces.
- Return structured errors instead of raw exceptions.




