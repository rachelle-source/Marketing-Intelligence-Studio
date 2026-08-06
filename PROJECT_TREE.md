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
│   │   ├── research_service.py     ResearchService       — TODO: implementation (needs backend/reddit)
│   │   ├── ai_service.py           AIService             — TODO: Claude integration + Prompt Builder
│   │   ├── knowledge_service.py    KnowledgeService      — TODO: implementation
│   │   ├── export_service.py       ExportService         — TODO: Markdown exporter, then DOCX/HTML/PDF
│   │   └── settings_service.py     SettingsService       — implemented (SQLite-backed)
│   ├── reddit/                  TODO: placeholder for the existing Reddit scraper
│   └── lint/                    TODO: placeholder for the existing draft linter
│
├── frontend/                    TODO: desktop GUI — not built yet
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
├── output/                      generated exports, git-ignored except .gitkeep
├── data/                        SQLite database file, git-ignored except .gitkeep
├── tests/                       pytest suite for the backend foundation
├── docs/                        product/design/engineering doc packs
│   ├── 00_foundation.md
│   ├── 01_design.md
│   └── 02_engineering.md
│
├── conftest.py                  makes backend/* importable under pytest
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_TREE.md              this file
```

## Pending (explicit TODOs — see README.md for details)

- Reddit scraper source → `backend/reddit/`
- Draft linter source → `backend/lint/`
- Claude API integration + Prompt Builder → `backend/services/ai_service.py`
- Markdown exporter → `backend/services/export_service.py`
- Desktop GUI → `frontend/`
- Real client briefs for `korr`, `8msolar`, `solartime`, `crinkletime`, `unsexy_businessmen`
