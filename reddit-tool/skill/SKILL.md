# Reddit Reply Tool

Scrapes Reddit threads for a client, filters them for reply-worthiness, drafts brand-voice
replies, lints them, and saves output to a markdown file. No API key required.

**Project root:** `REDDIT_TOOL_PATH`

## Trigger

`/reddit-tool` or `/reddit-tool <client-name>`

---

## Steps — execute in this exact order every run

### Step 1: Client selection

If a client name was passed as an argument to this skill, use it. Skip to Step 2.

Otherwise, run:

```bash
python -c "from pathlib import Path; print('\n'.join(sorted(f.stem for f in Path('REDDIT_TOOL_PATH/clients').glob('*.json') if not f.stem.startswith('_'))))"
```

Ask the user: "Which client? Available clients: [list the output above]"

Wait for their answer before continuing.

---

### Step 2: Scrape

Run:

```bash
python "REDDIT_TOOL_PATH/scrape.py" --client <client-name> --json-out "REDDIT_TOOL_PATH/drafts/.threads.json"
```

Report the number of threads fetched (shown in stderr output). If stderr shows an error
loading the client config, or if 0 threads were written, stop and tell the user — do not
continue to Step 3.

---

### Step 3: Load client config

Read `REDDIT_TOOL_PATH/clients/<client-name>.json`. You will need `client_name`,
`brand_context`, and `keywords` for the next steps.

---

### Step 4: Filter threads

Read `REDDIT_TOOL_PATH/drafts/.threads.json`. For each thread, score it 1–10.

**Score 7–10 (worth replying to):**
- Genuine question the client's expertise directly answers
- Real engagement (upvotes or comments > 0)
- Factual reply would add clear value
- Topic matches the client's keywords and subject space
- Passes any FILTERING criteria described in `brand_context`

**Score 5–6 (borderline — skip):**
- Loosely relevant but no clear question to answer
- Engagement exists but a reply adds marginal value

**Score 1–4 (skip):**
- Off-topic or only loosely related
- Rant, complaint, or debate with no answerable question
- Zero engagement
- Already fully and well answered
- A reply would look like brand promotion

Print one line per thread:
`[score/10] r/<subreddit> — <reason> — "<title, truncated to 60 chars>"`

Only proceed with threads scoring ≥ 7. If no threads pass, tell the user and stop.

---

### Step 5: Draft replies

For each passing thread, write a Reddit comment that:

- Is 50–150 words
- Sounds like a knowledgeable individual, not a brand or content writer
- Directly answers the question or addresses the point raised
- Includes one concrete fact, data point, or specific piece of guidance
- Ends with an open-ended question that invites others' experience (not a yes/no question)
- Uses peer voice: "I've found", "in my experience", "seems like" — not "you should", "you need to", "you must"
- Contains no emojis
- Contains no CTA phrases: "let me know", "feel free to", "happy to discuss", "happy to chat", "DM me", "reach out", "don't hesitate"
- Follows ALL voice rules, banned words, and punctuation rules in `brand_context`
- Does not mention the client brand by name unless the thread explicitly asks for installer/provider recommendations

---

### Step 6: Lint each draft

Do this one draft at a time: write to temp file, lint, record result, then move to the next.

For each draft, write it to `REDDIT_TOOL_PATH/drafts/.draft_tmp.txt`, then run:

```bash
python "REDDIT_TOOL_PATH/scripts/lint_draft.py" <client-name> --file "REDDIT_TOOL_PATH/drafts/.draft_tmp.txt"
```

The script exits 0 on pass, 1 on fail, and prints a summary plus any warnings.

If lint fails: redraft once, prepending this to your prompt:
"The previous draft failed these lint checks — fix all of them in your new draft: [paste warnings here]"

Run lint again on the redraft. Show the verdict (PASS or FAIL) for each draft. If the
redraft also fails lint, include it in the output with FAIL status and add a note:
*(two attempts — review carefully)*

---

### Step 7: Write output file

Save to `REDDIT_TOOL_PATH/drafts/<YYYY-MM-DD>-<client-name>.md` using today's date.

Use this format:

```markdown
# Reddit Drafts — <Client Name>
_Generated: <YYYY-MM-DD>_

---

## <Thread Title>
**Subreddit:** r/<subreddit>  
**URL:** <url>  
**Score:** <filter score>/10 — <filter reason>  
**Lint:** PASS (score: <lint score>/100 — lower is better)

> <draft text, wrapped at 100 chars>

---

## <Thread Title>
**Subreddit:** r/<subreddit>  
**URL:** <url>  
**Score:** <filter score>/10 — <filter reason>  
**Lint:** FAIL (score: <lint score>/100 — lower is better) — <comma-separated warnings>

> <draft text>

---
```

Order threads by filter score descending (highest first). Include lint failures — flag
them clearly so the user can decide whether to use them.

Print the output file path when done.
