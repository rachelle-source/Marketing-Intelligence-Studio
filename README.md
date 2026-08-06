# Marketing Intelligence Studio

> Research once. Create everywhere.

A desktop application that centralizes client marketing knowledge, runs
research (starting with Reddit), and generates on-brand content through
Claude — with every AI request flowing through one auditable service.

This repository currently contains the **backend foundation only**: folder
structure, configuration, logging, database schema, and service interfaces.
There is no desktop UI yet, and the Reddit scraper / draft linter have not
been added to this repo yet (see [Pending work](#pending-work)).

## Documentation

The product/design/engineering specs this foundation was built from:

- [`docs/00_foundation.md`](docs/00_foundation.md) — product vision, roadmap, architecture, database schema, AI pipeline
- [`docs/01_design.md`](docs/01_design.md) — UI guidelines, feature list, internal API (service) design
- [`docs/02_engineering.md`](docs/02_engineering.md) — coding standards, security, testing, deployment

## Architecture

```
UI (future)  ->  Services  ->  Database / Claude API
```

The UI never talks to the database or an external API directly — it only
calls the services below. All AI requests go through `AIService`.

```
backend/
├── config.py            # AppConfig: env/.env-driven settings (paths, log level, API key)
├── core/
│   ├── logging_config.py  # rotating file + console logging setup
│   ├── errors.py           # AppError / NotFoundError / ValidationError / ServiceError
│   ├── database.py         # SQLite schema + connection management
│   └── bootstrap.py        # initialize_app(): wires config + logging + db together
├── models/                # pydantic domain models (one module per DB table)
├── services/              # service interfaces (the "Internal API")
│   ├── client_service.py     # ClientService        — TODO: implementation
│   ├── research_service.py   # ResearchService       — TODO: implementation (needs backend/reddit)
│   ├── ai_service.py         # AIService             — TODO: Claude integration + Prompt Builder
│   ├── knowledge_service.py  # KnowledgeService      — TODO: implementation
│   ├── export_service.py     # ExportService         — TODO: Markdown exporter, then DOCX/HTML/PDF
│   └── settings_service.py   # SettingsService       — implemented (SQLite-backed)
├── reddit/                # TODO: placeholder for the existing Reddit scraper
└── lint/                  # TODO: placeholder for the existing draft linter

frontend/    # TODO: desktop GUI — not built yet
clients/     # per-client JSON config files (none committed yet)
logs/        # app.log (rotating), git-ignored except .gitkeep
output/      # generated exports, git-ignored except .gitkeep
data/        # SQLite database file, git-ignored except .gitkeep
tests/       # pytest suite for the foundation
docs/        # the three doc packs above
```

## Architectural decisions

**Why services are interfaces (`ABC`), not implementations.**
Per the Engineering Pack: "do not invent major features without approval."
`ClientService`, `ResearchService`, `AIService`, `KnowledgeService`, and
`ExportService` define the exact method signatures from the Design Pack's
Internal API section, but their bodies are `TODO` — there's no real feature
behind them yet (no Claude integration, no Reddit scraper source in this
repo, no exporters). Building concrete logic now would mean guessing at
behavior nobody has specified.

**Why `SettingsService` is the one exception.**
It ships as a working `SQLiteSettingsService` because the foundation itself
needs a place to read/write preferences from day one — it doesn't depend on
anything not yet built.

**Why `BrandProfiles` is a separate table/model from `Clients`.**
The Foundation Docs' Core Tables list names them separately, so the "Client
Schema" fields are split accordingly: `clients` holds company/website/
industry/products/competitors; `brand_profiles` holds voice/tone/SEO
keywords/avoid words/prompt templates, keyed by `client_id`.

**Why `settings` has no `client_id`.**
Every other table belongs to a client per the Foundation Docs, but
`settings` holds app-wide preferences (theme, default AI model, export
preferences) — those aren't client data.

**Why pydantic models instead of dicts.**
Each model module (`backend/models/*.py`) defines a `*Create` /
`*Update` / stored variant per entity, matching the Design Pack's "services
communicate through well-defined interfaces" rule and the Engineering Pack's
type-hints requirement.

**Why a `data/` folder beyond the originally-named folders.**
The database needs a home that isn't `output/` (generated exports) or
`logs/`. `data/` holds only the SQLite file.

**Why config and logging are separate from the database.**
`AppConfig` (env-driven secrets/paths) and `configure_logging` take plain
arguments rather than reaching for a global singleton, so each piece is
independently testable. `backend/core/bootstrap.py` is the one place that
wires them together — a future CLI or GUI entrypoint calls
`initialize_app()` once and gets back an `AppContext` with everything ready.

**Why structured errors (`backend/core/errors.py`).**
The Design Pack requires "structured errors instead of raw exceptions" so a
future UI can distinguish "not found" from "invalid input" from "something
broke," instead of parsing exception messages.

## Pending work

These are placeholders, not implementations — deliberately left as `TODO`
so no functionality is invented ahead of a real spec or source:

- **Reddit scraper** (`backend/reddit/`) — waiting on the existing
  `scrape.py` source to be added to this repo.
- **Draft linter** (`backend/lint/`) — waiting on the existing
  `lint_draft.py` source to be added to this repo.
- **Claude API integration** (`AIService.generate`)
- **Prompt Builder** (`AIService.build_prompt`)
- **Markdown exporter** (`ExportService.export_markdown`)
- **Desktop GUI** (`frontend/`)

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in MIS_CLAUDE_API_KEY once the AI integration exists
pytest
```
