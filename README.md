# Marketing Intelligence Studio

> Research once. Create everywhere.

A desktop application that centralizes client marketing knowledge, runs
research (starting with Reddit), and generates on-brand content through
Claude — with every AI request flowing through one auditable service.

**Status: Reddit Research is the primary, polished workflow.** Type a
client and a topic, click Run, get back a real report — ranked, deduped,
spam-filtered threads with extracted questions/pain points/buying
signals/competitor mentions, saved permanently to that client's knowledge
base. AI Writer, Knowledge Extraction, and Markdown Export are intentionally
still `TODO` — this iteration deepened one workflow instead of adding more
half-finished ones. See [Pending work](#pending-work).

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

## Reddit Research (v2 — the primary workflow)

`backend/reddit/RedditService` implements `ResearchService` on top of
[PRAW](https://praw.readthedocs.io/) — not the legacy `scrape.py` referenced
earlier in this project's history, which was never actually provided despite
being requested repeatedly.

Pipeline for `RedditService.research(client_id, topic)`:

1. Load the client's `seo.json` keywords, `competitors.json` names, and
   display name.
2. Expand the topic into a few keyword-paired search queries.
3. Search Reddit via PRAW for each query — **posts only, no comments yet**
   (the speed-critical step; see below). One failing query is logged and
   skipped rather than aborting the run; it only raises if every query
   fails.
4. Deduplicate (exact id + near-duplicate titles), filter spam, score
   relevance (keyword overlap + engagement — title/selftext only), and keep
   only the top `max_results` (10 by default).
5. **Only now** fetch comments — for those ≤10 surviving posts, not the
   full fetch (which can be 50-100+ posts across 4 query variants).
6. Extract customer questions, pain points, buying signals, and competitor
   mentions from every surviving post (now with comments attached).
7. `run_and_report` renders the result as a **market research brief**
   (`backend/reddit/report.py`), saves it into
   `clients/<slug>/knowledge/reddit.md`, and persists a `ResearchSession`
   row. `run_reddit_research` (the bare `ResearchService`-required method)
   is a thin wrapper around it for interface compliance.

### The brief itself

The report is written to be read by a marketing strategist, not a
developer — sections in priority order:

1. **Executive Summary** — a short paragraph: how many discussions were
   reviewed, how many pain points/buying signals/competitor mentions were
   found, the most-discussed competitor (if any), and any recurring terms
   that showed up in more than one discussion.
2. **Key Findings** — up to 5 standout items (capped at 2 per category:
   pain point / buying signal / competitor mention / question), pulled from
   the highest-relevance discussions first — read this and stop if that's
   all the time you have.
3. **Customer Pain Points** / **Buying Signals & Purchase Intent** —
   every distinct point found, grouped under one heading each and
   deduplicated, instead of repeating the same structure once per thread.
4. **Competitive Landscape** — competitors mentioned, aggregated with a
   mention count and which subreddits, most-mentioned first.
5. **Questions From the Community** — capped at 8 with a "...and N more"
   note, so a long list of near-identical questions doesn't dominate the
   page.
6. **Sources** and a one-line *Methodology* note — thread titles/links and
   the search/dedup/spam stats live here, at the very bottom, not mixed
   into the narrative above.

Relevance scores, comment counts, and query-variant lists — useful for
debugging, meaningless to a client — never appear in the narrative sections;
they're either dropped entirely or folded into that closing Methodology
line. Everything in the brief is copied or counted directly from real
extracted data; nothing is generated or invented (there's no LLM in this
pipeline yet — see `AIService`, still `TODO`).

Requires `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (see `.env.example`) —
get them at https://www.reddit.com/prefs/apps. Everything is unit-tested
against mocked PRAW objects (`tests/reddit_fakes.py`); one real-network test
(`tests/integration/test_reddit_live.py`) is skipped unless those
credentials are actually set — this project's own environment can't reach
`reddit.com` at all (network policy), so that test has never been run here,
only designed to run on a developer's machine.

**Every research run permanently adds to the client's knowledge base.** The
first run replaces the scaffolded "Status: empty" placeholder in
`knowledge/reddit.md`; every run after that appends a new dated section —
it's a running research log, not a one-off snapshot that gets overwritten.

## Desktop GUI (v2)

`python -m frontend.app` opens a plain Tkinter window: a client list (from
`clients/`), a marketing tool list, a topic field, and a Run button. Still
not styled — this version optimizes for "does it work well," not "does it
look good."

Only **Reddit Research** is wired to a real backend call; the other three
tools are listed (so the team can see what's coming) but clicking Run
reports plainly that they're not implemented yet, rather than faking output.

Research runs on a background thread — the window stays responsive (and the
Run button is visibly disabled) for however long the search takes, instead
of freezing. Pressing Enter in the topic field runs it too. The output pane
shows the full rendered report (every kept thread, its questions/pain
points/buying signals/competitor mentions, and a link), not just a one-line
count — and the status bar reports how long the run took.

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

**Why comment-fetching is deferred until after ranking.** Fetching a post's
comments is its own PRAW network round trip — the single biggest cost in a
Reddit search. The original v1 fetched comments for every post returned by
every query variant (up to ~100 network calls for a 4-query, 25-post-limit
search). `select_top_posts` now ranks on title/selftext alone (comments were
never used for relevance scoring anyway) and `fetch_top_comments` is only
called for the ≤10 posts that survive — typically cutting comment-fetch
calls by 10x+ with no loss of ranking accuracy.

**Why one failing search query doesn't fail the whole run.** With 4 query
variants per topic, a single transient PRAW/network error used to abort
everything and lose posts the other 3 queries had already found.
`_search_all_queries` now catches `RedditSearchError` per query, logs and
skips it, and only re-raises if every single query failed — partial results
are still useful; losing them to one blip isn't worth it.

**Why the report is Markdown text, not a data structure the GUI has to
render.** `render_markdown_report` produces the exact text both the GUI's
output pane and `knowledge/reddit.md` show — one rendering path, so the
report a marketer reads on-screen is byte-for-byte what gets saved for
later. No templating engine, no second format to keep in sync.

**Why `knowledge/reddit.md` accumulates instead of getting overwritten.**
A knowledge base that erases yesterday's research every time someone runs
a new query isn't a knowledge base. `save_report_to_knowledge_base` detects
the scaffolded placeholder (replaces it once) and otherwise appends a new
dated section — the file is a running log a team member can scroll through.

**Why the brief groups findings by category instead of repeating a
per-thread block.** The original layout listed every kept post with its own
"Questions / Pain points / Buying signals" sub-list — readable for
debugging, but it made a reader piece together "what are customers actually
saying" by re-reading N thread blocks. Grouping every pain point together,
every buying signal together, etc. (deduplicated) means a strategist reads
one coherent list per theme instead of reassembling it themselves.

**Why Key Findings is capped at 5, 2 per category.** Without a cap, "Key
Findings" would just be a shorter copy of the sections below it. The 2-per-
category limit forces variety (not five near-identical pain points) while
still letting one unusually rich top-relevance thread contribute more than
one *kind* of finding — that's still "most important first," just expressed
across categories rather than restricted to one thread each.

**Why "recurring terms" and "top competitor" are the only synthesized
lines, and both are literal counts.** A real market-research brief usually
opens with a synthesized insight ("customers are frustrated with X"). There
is no LLM in this pipeline to write that honestly — `AIService` is still
`TODO`. Rather than fabricate confident-sounding prose, the executive
summary limits itself to two mechanically-derived, defensible statements:
which competitor was mentioned most (a plain count) and which words recur
across 2+ distinct pain points/buying signals (a plain word-frequency
count, stopword-filtered). Both are labeled as counts, not claims.

**Why relevance scores, comment counts, and query variants disappear from
the narrative.** They're real numbers the pipeline uses internally
(ranking, dedup, spam-filtering) but meaningless to someone deciding what to
do about customer feedback. They're not lost — they live in the one-line
Methodology footer — just no longer competing for attention with the actual
findings.

**Why Run happens on a background thread.** Tkinter has one UI thread; a
network-bound PRAW search taking a few seconds would otherwise freeze
window redraws entirely (appearing as "Not Responding"). `_on_run_click`
now starts a daemon thread and polls a thread-safe queue via `after()` —
the standard safe pattern for getting a background result back onto a Tk
widget. The Run button disables for the duration and a double-click/repeat
Enter while running is ignored outright, rather than queuing a second
concurrent search.

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
