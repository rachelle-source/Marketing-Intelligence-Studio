# Clients

Each client has its own directory containing structured intelligence used for research
and content generation:

```
clients/<slug>/
├── profile.json        company/business info
├── prompts.json        voices, content-type structures, CTAs, quality checklist
├── seo.json            keyword clusters, terms to avoid
├── competitors.json    positioning, named/conceptual competitors, rules
└── knowledge/
    ├── faq.md
    ├── objections.md
    ├── messaging.md
    ├── terminology.md
    ├── products.md
    ├── blog_topics.md
    ├── research.md
    └── reddit.md
```

This is a superset of the `backend.models.client.Client` /
`backend.models.brand_profile.BrandProfile` database schema — everything here is
file-based today; a future `ClientService` implementation will read/sync it into the
database.

## Client status

| Slug | Status | Source |
|---|---|---|
| `kore` | **Populated** | `kore-content-hub` skill document (Brand Guidelines 01/01/2026, Message House Feb 2026) — provided directly by user, 2026-08-07 |
| `mcfie` | **Populated** | `mcfie-content-hub` skill (installed locally) — McFie Insurance voices, core concepts, phrases to avoid, social guide — plus `insurance-binder-builder` skill document (educational lead-magnet binder format), provided directly by user, 2026-08-07 |
| `korr` | **Populated** | `KORR_Reddit_Skill.pdf` (KORR Medical Technologies facts extracted from a personal Reddit-growth skill doc) — provided directly by user, 2026-08-07 |
| `8msolar` | **Populated** | `8msolar-content-hub` skill document — provided directly by user, 2026-08-07 |
| `solartime` | Scaffold only | No source data found anywhere |
| `crinkletime` | Scaffold only | No source data found anywhere |
| `unsexy_businessmen` | Scaffold only | No source data found anywhere |

"Scaffold only" means every file exists with the correct structure, but all content
fields are empty/`null` with a `"status": "no_source_data"` marker and a `notes` field
explaining why — no brand voice, competitors, or messaging has been invented for these
five. Replace them with real client briefs before using them for content generation.

`research.md` and `reddit.md` are intentionally empty for **every** client, including
`kore` and `mcfie` — no primary research or Reddit research has actually been run yet
(`backend/reddit/` is still a TODO pending the real scraper source).

## Reddit tool configuration (`reddit_config`)

`reddit-tool/` (see its own README) is a separate, already-working Reddit reply tool
vendored into this repo — it is not rewritten here. It needs a small config per client
(`subreddits`, `keywords`, `brand_context`, `notify_email`, `max_threads`, `sort`) that
used to require hand-editing its JSON directly. Instead, `backend/reddit/config_generator.py`
generates `reddit-tool/clients/<slug>.json` from this repo's own client knowledge, so
that knowledge stays the single source of truth:

- `keywords` comes from `seo.json`'s `primary_keywords`.
- `client_name` and `brand_context` come from `profile.json`'s `client_name`/`company`,
  `description`/`core_promise`, and `reddit_config.tone`.
- `subreddits`, `tone`, `notify_email`, `max_threads`, and `sort` come from a
  `reddit_config` object added to `profile.json` — these are operational choices (which
  communities to watch, who gets notified), not marketing facts, so they can't be derived
  from anything else already in `clients/`. `status: "generated_default"` on that object
  means the subreddit list is the generator's topic-relevance starting point, not a
  client-confirmed decision — review it before relying on live Reddit research.

To (re)generate every client's config: `python -m backend.reddit.config_generator`.
To generate one: `python -m backend.reddit.config_generator <slug>`.
