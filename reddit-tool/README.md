# Reddit Reply Tool for Claude Code

A Claude Code skill that scrapes Reddit, scores threads for reply-worthiness, drafts
brand-voice replies, lints them automatically, and saves everything to a dated markdown
file. No Reddit API key required.

## What it does

1. Scrapes configured subreddits via the public Reddit API
2. Scores each thread 1-10 for whether a factual reply adds value
3. Drafts replies that sound like a knowledgeable individual, not a brand
4. Lints each draft for word count, tone, banned phrases, and Reddit-native style
5. Saves output to `drafts/YYYY-MM-DD-<client>.md`

## Requirements

- Python 3.8+
- [Claude Code](https://claude.ai/code)

## Setup

### 1. Place the project

Put this folder anywhere on your machine and note the full path.

Examples:
- Mac/Linux: `/Users/yourname/Projects/reddit-tool`
- Windows: `C:\Users\yourname\Projects\reddit-tool`

### 2. Install Python dependencies

```bash
cd reddit-tool
pip install -r requirements.txt
```

### 3. Install the Claude Code skill

**Mac/Linux:**
```bash
mkdir -p ~/.claude/skills/reddit-tool
cp skill/SKILL.md ~/.claude/skills/reddit-tool/SKILL.md
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\reddit-tool"
Copy-Item "skill\SKILL.md" "$env:USERPROFILE\.claude\skills\reddit-tool\SKILL.md"
```

Then open the installed `SKILL.md` and replace every instance of `REDDIT_TOOL_PATH`
with your actual project path (no trailing slash).

Mac/Linux example — replace:
```
REDDIT_TOOL_PATH
```
with:
```
/Users/yourname/Projects/reddit-tool
```

Windows example — replace:
```
REDDIT_TOOL_PATH
```
with:
```
C:\Users\yourname\Projects\reddit-tool
```

### 4. Add your first client

Copy `clients/_template.json` to `clients/your-client-name.json` and fill it in.
The filename (without `.json`) is what you type when Claude Code asks which client to run.

The most important field is `brand_context` — it tells Claude how to write replies,
what to avoid, and what reference data to use. See the field description in `_template.json`.

### 5. Run it

Open Claude Code in any directory and type:

```
/reddit-tool
```

Claude will list your available clients and walk through the rest.

---

## Adding a new client to the linter

If your client needs custom lint rules (banned words, punctuation rules, etc.), add an
entry to the `PER_CLIENT_RULES` dict in `scripts/lint_draft.py`. The key is the
client filename slug (e.g. `"my-client"` for `clients/my-client.json`).

---

## Project structure

```
reddit-tool/
├── scrape.py               # CLI scraper — no API key needed
├── requirements.txt
├── skill/
│   └── SKILL.md            # Claude Code skill (install to ~/.claude/skills/reddit-tool/)
├── src/
│   ├── config.py           # Client config loader
│   ├── models.py           # Data models
│   └── scraper.py          # Reddit API client
├── scripts/
│   └── lint_draft.py       # Draft linter (CLI + importable module)
├── clients/
│   └── _template.json      # Copy this to add a new client
├── tests/                  # pytest test suite
└── drafts/                 # Output directory (gitignored)
```

---

## Running tests

```bash
pytest tests/
```
