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
│   │   ├── config_generator.py     RedditConfigGenerator: derives reddit-tool/clients/<slug>.json
│   │   │                           from a client's profile.json (reddit_config section) + seo.json
│   │   │                           — see reddit-tool/README.md; run via
│   │   │                           `python -m backend.reddit.config_generator [slug]`
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
│   ├── credential_setup.py         RedditSetupDialog — first-run "Connect to Reddit"
│   │                               dialog; no .env hand-editing required
│   └── app.py                      entrypoint: python -m frontend.app
│
├── clients/                     per-client intelligence (see clients/README.md)
│   ├── kore/                      populated — KORE Wireless (kore-content-hub skill doc)
│   ├── mcfie/                     populated — McFie Insurance (mcfie-content-hub + insurance-binder-builder skills)
│   ├── korr/                      populated — KORR Medical Technologies (KORR_Reddit_Skill.pdf)
│   ├── 8msolar/                   populated — 8MSolar (8msolar-content-hub skill doc)
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
├── reddit-tool/                  Vendored reddit-reply-tool project (scrapes threads, scores
│                                 reply-worthiness, drafts/lints brand-voice replies). Its own
│                                 independent project with its own tests/README — not rewritten.
│                                 clients/<slug>.json here is generated, not hand-edited — see
│                                 backend/reddit/config_generator.py.
├── logs/                        app.log (rotating), git-ignored except .gitkeep
├── output/                      NotebookLM-ready exports, one folder per client
│                                 (<slug>/<date>_<topic>.md), git-ignored except .gitkeep
├── data/                        SQLite database file, git-ignored except .gitkeep
├── tests/                       pytest suite for the backend foundation (pytest.ini scopes a
│                                 bare `pytest` here so it doesn't collide with reddit-tool/tests/)
├── docs/                        product/design/engineering doc packs
│   ├── 00_foundation.md
│   ├── 01_design.md
│   └── 02_engineering.md
│
├── packaging/                    standalone Windows/macOS app packaging (PyInstaller)
│   ├── pyinstaller.spec             build spec: bundles the interpreter + all deps
│   ├── build_windows.bat            local build script (run on Windows)
│   ├── build_macos.sh               local build script (run on macOS)
│   ├── INSTALL.md                   non-technical install/setup guide
│   └── assets/
│       ├── icon.ico                  Windows .exe icon
│       └── icon.icns                 macOS .app icon
├── Release/                      Version 1 distributable — see Release/README.md
│   ├── README.md                    what's inside, how to get/rebuild the app zips
│   └── HOW TO INSTALL.txt           non-technical install/setup guide
├── .github/workflows/
│   └── build-release.yml            CI: builds real .exe/.app on windows-latest/macos-latest
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
- Real client briefs for `solartime`, `crinkletime`, `unsexy_businessmen`
