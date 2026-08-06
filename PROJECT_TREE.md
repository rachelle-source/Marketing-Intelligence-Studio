# Project Tree

Authoritative structure reference. Update this file whenever top-level folders or the
per-client layout change.

```
Marketing-Intelligence-Studio/
├── backend/
│   ├── config.py               AppConfig (env/.env-driven settings)
│   ├── core/
│   │   ├── logging_config.py     rotating file + console logging
│   │   ├── errors.py             AppError hierarchy
│   │   ├── database.py           SQLite schema + connection management
│   │   └── bootstrap.py          initialize_app(): wires config+logging+db
│   ├── models/                  pydantic domain models (one module per DB table)
│   ├── services/                service interfaces (the "Internal API")
│   │   ├── client_service.py       ClientService        — TODO: implementation
│   │   ├── research_service.py     ResearchService       — implemented by backend/reddit/service.py
│   │   ├── ai_service.py           AIService             — TODO: Claude integration + Prompt Builder
│   │   ├── knowledge_service.py    KnowledgeService      — TODO: implementation
│   │   ├── export_service.py       ExportService         — TODO: Markdown exporter, then DOCX/HTML/PDF
│   │   └── settings_service.py     SettingsService       — implemented (SQLite-backed)
│   ├── reddit/                  Reddit research — implemented (PRAW-backed), v2
│   │   ├── client.py               mockable PRAW wrapper: fast post search + deferred
│   │   │                           per-post fetch_top_comments (speed optimization)
│   │   ├── query_builder.py        topic -> keyword-aware search queries
│   │   ├── analysis.py             dedup, spam filter, relevance ranking (select_top_posts),
│   │   │                           extraction (build_analyzed_post)
│   │   ├── client_context.py       loads a client's profile/seo/competitors.json
│   │   ├── report.py               renders RedditResearchReport -> Markdown; saves/appends
│   │   │                           into clients/<slug>/knowledge/reddit.md
│   │   ├── service.py              RedditService (ResearchService impl); per-query failure
│   │   │                           isolation; run_and_report() -> (session, markdown, saved_path)
│   │   ├── export.py               standalone NotebookLM-ready export:
│   │   │                           output/<client>/<date>_<topic>.md
│   │   ├── models.py               shared normalized data model
│   │   └── errors.py               RedditCredentialsError / RedditSearchError
│   └── lint/                    TODO: placeholder for the existing draft linter
│
├── frontend/                    Desktop GUI (Tkinter) — v4, plain but working
│   ├── client_discovery.py         reads clients/<slug>/profile.json
│   ├── tools.py                    marketing tool registry
│   ├── run_controller.py           (client, tool, topic) -> backend calls, Tk-free
│   ├── main_window.py              the Tk window; threaded Run, Enter-to-run, full
│   │                               report display, elapsed-time status, Save for
│   │                               NotebookLM / Open Export Folder / Copy Report buttons
│   ├── os_actions.py               open_in_file_manager() — cross-platform folder opener
│   └── app.py                      entrypoint: python -m frontend.app
│
├── clients/                     per-client intelligence (see clients/README.md)
│   ├── kore/                      populated — KORE Wireless (kore-content-writer skill)
│   ├── mcfie/                     populated — McFie Insurance (mcfie-content-hub skill)
│   ├── korr/                      scaffold only — no source data
│   ├── 8msolar/                   scaffold only — no source data
│   ├── solartime/                 scaffold only — no source data
│   ├── crinkletime/                scaffold only — no source data
│   ├── unsexy_businessmen/         scaffold only — no source data
│   └── <slug>/
│       ├── profile.json
│       ├── prompts.json
│       ├── seo.json
│       ├── competitors.json
│       └── knowledge/
│           ├── faq.md
│           ├── objections.md
│           ├── messaging.md
│           ├── terminology.md
│           ├── products.md
│           ├── blog_topics.md
│           ├── research.md
│           └── reddit.md
│
├── logs/                        app.log (rotating), git-ignored except .gitkeep
├── output/                      NotebookLM-ready exports, one folder per client
│                                 (<slug>/<date>_<topic>.md), git-ignored except .gitkeep
├── data/                        SQLite database file, git-ignored except .gitkeep
├── tests/                       pytest suite for the backend foundation
├── docs/                        product/design/engineering doc packs
│   ├── 00_foundation.md
│   ├── 01_design.md
│   └── 02_engineering.md
│
├── conftest.py                  makes backend/* importable under pytest; registers the
│                                 "integration" pytest marker
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_TREE.md              this file
```

## Pending (explicit TODOs — see README.md for details)

- Draft linter source → `backend/lint/`
- Claude API integration + Prompt Builder → `backend/services/ai_service.py`
- Markdown exporter → `backend/services/export_service.py`
- `ClientService` (real client CRUD/sync into the database)
- A styled, multi-panel desktop UI per the Design Pack (today's is plain)
- Real client briefs for `korr`, `8msolar`, `solartime`, `crinkletime`, `unsexy_businessmen`
