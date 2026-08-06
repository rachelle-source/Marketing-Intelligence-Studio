# Marketing Intelligence Studio

> Research once. Create everywhere.

A desktop application that centralizes client marketing knowledge, runs
research (starting with Reddit), and generates on-brand content through
Claude — with every AI request flowing through one auditable service.

**Status: first usable version.** The backend foundation, the client
intelligence structure, Reddit research (`RedditService`, real and working),
and a plain desktop GUI are all in place. AI Writer, Knowledge Extraction,
and Markdown Export are still `TODO` — see [Pending work](#pending-work).

Launch it with:

```bash
python -m frontend.app
```

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
│   ├── research_service.py   # ResearchService       — implemented by backend/reddit/service.py
│   ├── ai_service.py         # AIService             — TODO: Claude integration + Prompt Builder
│   ├── knowledge_service.py  # KnowledgeService      — TODO: implementation
│   ├── export_service.py     # ExportService         — TODO: Markdown exporter, then DOCX/HTML/PDF
│   └── settings_service.py   # SettingsService       — implemented (SQLite-backed)
├── reddit/                # Reddit research — implemented (PRAW-backed), see below
│   ├── client.py             # thin, mockable PRAW wrapper (search + normalize)
│   ├── query_builder.py      # topic -> keyword-aware search query variants
│   ├── analysis.py           # dedup, spam filter, relevance scoring, extraction
│   ├── client_context.py     # loads a client's seo.json/competitors.json
│   ├── service.py            # RedditService (ResearchService implementation)
│   └── models.py             # RedditPost/Comment/SearchResult/AnalyzedPost/Report
└── lint/                  # TODO: placeholder for the existing draft linter

frontend/    # Desktop GUI (Tkinter) — v1, see below
├── client_discovery.py      # reads clients/<slug>/profile.json
├── tools.py                 # the marketing tool registry
├── run_controller.py        # wires (client, tool, topic) -> backend calls, Tk-free
├── main_window.py           # the actual Tk window
└── app.py                   # entrypoint: python -m frontend.app

clients/     # per-client intelligence (profile/prompts/seo/competitors + knowledge/) — see clients/README.md
logs/        # app.log (rotating), git-ignored except .gitkeep
output/      # generated exports, git-ignored except .gitkeep
data/        # SQLite database file, git-ignored except .gitkeep
tests/       # pytest suite (backend + frontend + reddit)
docs/        # the three doc packs above
```

See [`PROJECT_TREE.md`](PROJECT_TREE.md) for the full, current file tree.

## Reddit Research (v1)

`backend/reddit/RedditService` implements `ResearchService` on top of
[PRAW](https://praw.readthedocs.io/) — not the legacy `scrape.py` referenced
earlier in this project's history, which was never actually provided despite
being requested repeatedly.

Pipeline for `RedditService.research(client_id, topic)`:

1. Load the client's `seo.json` keywords and `competitors.json` names.
2. Expand the topic into a few keyword-paired search queries.
3. Search Reddit via PRAW, normalize posts + top-level comments.
4. Deduplicate (exact id + near-duplicate titles) and filter spam.
5. Score relevance (keyword overlap + engagement) and drop low scorers.
6. Extract customer questions, pain points, buying signals, and competitor
   mentions from every surviving post.
7. Return a `RedditResearchReport`; `run_reddit_research` (the
   `ResearchService`-required method) additionally persists a
   `ResearchSession` row summarizing the run.

Requires `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (see `.env.example`) —
get them at https://www.reddit.com/prefs/apps. Everything is unit-tested
against mocked PRAW objects (`tests/reddit_fakes.py`); one real-network test
(`tests/integration/test_reddit_live.py`) is skipped unless those
credentials are actually set — this project's own environment can't reach
`reddit.com` at all (network policy), so that test has never been run here,
only designed to run on a developer's machine.

## Desktop GUI (v1)

`python -m frontend.app` opens a plain Tkinter window: a client list (from
`clients/`), a marketing tool list, a topic field, and a Run button. Not
styled — this version optimizes for "does it work," not "does it look
good."

Only **Reddit Research** is wired to a real backend call today; the other
three tools are listed (so the team can see what's coming) but clicking Run
reports plainly that they're not implemented yet, rather than faking output.

## Architectural decisions

**Why most services are still interfaces (`ABC`), not implementations.**
Per the Engineering Pack: "do not invent major features without approval."
`ClientService`, `AIService`, `KnowledgeService`, and `ExportService` define
the exact method signatures from the Design Pack's Internal API section, but
their bodies are `TODO` — there's no real feature behind them yet (no Claude
integration, no exporters). Building concrete logic now would mean guessing
at behavior nobody has specified.

**Why `SettingsService` and `ResearchService` are the two exceptions.**
`SettingsService` ships as a working `SQLiteSettingsService` because the
foundation itself needs a place to read/write preferences from day one.
`ResearchService` ships as `RedditService` (PRAW-backed) because it was
explicitly commissioned, in detail, rather than left to guesswork — see
"Reddit Research (v1)" above.

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

**Why `clients/` is file-based (JSON + Markdown) rather than only living in
the database.** Client intelligence — brand voice, SEO, competitors,
knowledge base — needs to be authored, reviewed, and diffed by humans before
any service reads it. Plain files under version control support that; the
database schema stays the sync target for a future `ClientService`, not the
source of truth for this content.

**Why only `kore` and `mcfie` have real content.** Every other client
(`korr`, `8msolar`, `solartime`, `crinkletime`, `unsexy_businessmen`) has no
existing brand/business data anywhere in this repo, its git history, or any
installed skill — confirmed by an explicit search before writing anything.
Rather than invent plausible-sounding brand voice or competitors for them,
they ship as structurally-correct scaffolds with `"status": "no_source_data"`
and empty fields. See `clients/README.md` for the per-client breakdown.

**Why PRAW instead of the legacy scraper.** The original `scrape.py`
referenced early in this project's history was requested from the user
three separate times and never actually provided. Given explicit direction
to stop waiting on it, `RedditService` is built on PRAW, the official Reddit
API client, instead.

**Why the analysis pass is lexicon/heuristic-based, not ML or Claude-based.**
Deterministic keyword/phrase matching for relevance scoring, pain points,
buying signals, and competitor mentions has no external dependency or cost,
runs offline, and is fully unit-testable with plain assertions. A
Claude-backed version would likely extract more nuanced signal, but that
depends on the still-`TODO` `AIService`/Claude integration — this is the
honest v1, not a placeholder pretending to be smarter than it is.

**Why `RedditService` upserts a minimal `clients` row before saving a
session.** `research_sessions.client_id` has a foreign key against
`clients.id`, but clients live as files (`clients/<slug>/`), not database
rows — there's no `ClientService` syncing them yet. Rather than drop the FK
(weakening a constraint the Foundation Docs call for) or block Reddit
research on building full client CRUD, `RedditService._save_session` upserts
a bare `clients` row (`id` = slug) first. This is a deliberate bridge, not a
long-term design — flagged here so it isn't mistaken for `ClientService`.

**Why Reddit credentials are read directly from `REDDIT_*` env vars, not
through `AppConfig`.** `AppConfig`'s fields are all `MIS_`-prefixed by
convention. Reddit's own ecosystem (PRAW docs, tutorials) universally uses
unprefixed `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET`, so `RedditClient` reads
those directly — it doesn't depend on `AppConfig` at all, which also keeps
it trivially constructible in tests without touching the config system.

**Why Tkinter for the GUI.** It's stdlib (no new packaging dependency),
ships with the Windows/macOS Python installers the Engineering Pack's
PyInstaller plan already targets, and is plain enough to satisfy "does not
need to be beautiful yet" without pulling in a browser runtime or a second
language toolchain. The Design Pack's eventual dark-mode/multi-panel UI can
replace this window's contents later without touching `run_controller.py`
or anything below it.

**Why `run_controller.py` is Tk-free.** Only `main_window.py` imports
`tkinter`. Every decision about *what* Run should do lives in
`RunController`, tested with zero GUI dependency — `main_window.py` is
intentionally thin enough that its own tests are just "does it build and
wire up correctly," not "is the business logic right."

**Why unavailable tools stay visible instead of being hidden.** Per the
Design Pack's UI rule to never hide what's happening: a team member should
be able to see the whole intended toolset (AI Writer, Knowledge Extraction,
Markdown Export) and get a clear "not implemented yet" on Run, rather than
wonder if the tool is missing or broken.

## Pending work

These are placeholders, not implementations — deliberately left as `TODO`
so no functionality is invented ahead of a real spec or source:

- **Draft linter** (`backend/lint/`) — waiting on the existing
  `lint_draft.py` source to be added to this repo.
- **Claude API integration** (`AIService.generate`)
- **Prompt Builder** (`AIService.build_prompt`)
- **Markdown exporter** (`ExportService.export_markdown`)
- **`ClientService`** — real client CRUD/sync into the database (see the
  `RedditService` FK-bridge note above)
- **Real client briefs** for `korr`, `8msolar`, `solartime`, `crinkletime`,
  `unsexy_businessmen`
- **A styled, multi-panel desktop UI** per the Design Pack — today's window
  is intentionally plain

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in REDDIT_CLIENT_ID/SECRET; MIS_CLAUDE_API_KEY once AI integration exists
pytest
python -m frontend.app
```

Notes on this project's own dev environment (not requirements for yours):

- The GUI needs a system Tk install — `python3-tk` on Debian/Ubuntu; bundled
  by default on Windows/macOS Python installers.
- Running the GUI tests headlessly (no physical display) needs a virtual
  display server, e.g. `xvfb-run -a pytest`.
