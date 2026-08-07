# Setting Up the Reddit Reply Tool

This is a **separate, more advanced tool** from the main Marketing Intelligence Studio
app. It scrapes Reddit, drafts brand-voice replies, and lints them — but unlike the
main app, it needs a few things installed on your computer first. This guide assumes
you've never used a command line before and walks through every step.

**Total time:** about 20-30 minutes, once, per computer. Budget more time the first
time through — after that, running it takes seconds.

## What you'll need

1. **Python** (a programming language the tool runs on) — free, Step 1 below.
2. **Claude Code** (the AI tool that does the scoring/drafting/linting) — needs a
   **paid Claude plan** (Pro, Max, Team, or Enterprise). A free claude.ai account is
   **not** enough. If your team doesn't already have one of these, talk to whoever
   manages your team's software subscriptions before continuing — Step 2 requires it.
3. This `reddit-tool` folder — it's already included right next to the main app, inside
   the same folder you unzipped. No separate download needed.
4. About 20-30 minutes for the one-time setup below.

---

## Step 1: Install Python

### Windows

1. Go to **python.org/downloads** in your browser.
2. Click the yellow **"Download Python"** button (it detects Windows automatically).
3. Open the downloaded file. **Important:** on the very first screen, check the box
   at the bottom that says **"Add python.exe to PATH"** before clicking "Install Now."
   If you skip this, nothing later in this guide will work, and you'll need to
   reinstall Python to fix it.
4. Click through the rest with the default options.

### Mac

1. Go to **python.org/downloads** in your browser.
2. Click the yellow **"Download Python"** button (it detects macOS automatically).
3. Open the downloaded `.pkg` file and click through the installer with default
   options.

### Check it worked

- **Windows:** Press the Windows key, type `PowerShell`, press Enter. In the black/blue
  window that opens, type `python --version` and press Enter.
- **Mac:** Press `Cmd + Space`, type `Terminal`, press Enter. In the window that opens,
  type `python3 --version` and press Enter.

Either way, you should see something like `Python 3.12.x`. If instead you see an error
like "command not found," close the window, reopen a fresh one (Python needs a new
window to be recognized), and try again. Still stuck — reinstall Python and make sure
you checked the "Add to PATH" box (Windows) mentioned above.

---

## Step 2: Install Claude Code

Claude Code runs from the same window (PowerShell or Terminal) you just used.

### Windows

In PowerShell, paste this and press Enter:

```
irm https://claude.ai/install.ps1 | iex
```

(If you accidentally opened Command Prompt instead of PowerShell — the window says
`C:\...>` with no `PS` in front — use this instead:
`curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd`)

### Mac

In Terminal, paste this and press Enter:

```
curl -fsSL https://claude.ai/install.sh | bash
```

### First-time login

1. Close that window and open a fresh one (same steps as Step 1's "Check it worked").
2. Type `claude` and press Enter.
3. Your browser opens automatically — log in with your Claude account (the paid plan
   from "What you'll need" above).
4. Once logged in, come back to the window — you're ready. You won't need to log in
   again on this computer.

Type `claude --version` any time to confirm it's installed correctly.

---

## Step 3: Install the tool's Python dependencies

Still in the same PowerShell/Terminal window:

1. Navigate into the `reddit-tool` folder. Type `cd ` (with a trailing space), then
   drag the `reddit-tool` folder from your file explorer directly into the window —
   its full path fills in automatically — then press Enter.
2. Type this and press Enter:

   ```
   pip install -r requirements.txt
   ```

   (On Mac, if that fails, try `pip3 install -r requirements.txt` instead.)

You'll see some text scroll by ending in something like "Successfully installed ...".
That's it for this step.

---

## Step 4: Install the Claude Code skill

Still in the same window, inside the `reddit-tool` folder, type:

```
python install_skill.py
```

(Mac: `python3 install_skill.py` if the first one fails.)

This one command sets everything up — it finds this folder automatically and connects
it to Claude Code. You'll see a confirmation message ending in "Next: open Claude Code
in any folder and type /reddit-tool."

---

## Step 5: Put in your own email

Each client's config file has a `notify_email` field that needs to say **your** email,
not a placeholder. This field isn't used to send anything automatically — it's just a
label — but it needs to say something real.

1. Open the `reddit-tool/clients` folder in your file explorer.
2. Pick the file for the client you'll be working on (e.g. `kore.json`) and open it —
   right-click, "Open with," choose Notepad (Windows) or TextEdit (Mac).
3. Find the line that says:

   ```
   "notify_email": "REPLACE-WITH-YOUR-EMAIL@example.com",
   ```

4. Replace the placeholder between the quotes with your real email address, keeping
   the quotes exactly as they are. For example:

   ```
   "notify_email": "yourname@keystonedigitalservices.com",
   ```

5. Save the file (Ctrl+S / Cmd+S) and close it. Repeat for each client you'll work with.

---

## Step 6: Run it

1. Open a fresh PowerShell/Terminal window (same steps as before).
2. Type `claude` and press Enter to start Claude Code.
3. Type:

   ```
   /reddit-tool
   ```

4. Claude Code lists the available clients and asks which one you want. Type the name
   (e.g. `kore`) and press Enter.
5. Watch the terminal — it scrapes Reddit, scores each thread, drafts replies, and
   lints them. This takes anywhere from 30 seconds to a couple of minutes.
6. When it's done, it prints the location of a saved file, something like
   `reddit-tool/drafts/2026-08-07-kore.md`. Open that file (Notepad/TextEdit, or drag
   it into Word) to read the drafted replies.

Each draft shows which Reddit thread it's replying to, a link to that thread, a
relevance score, and a PASS/FAIL from the style checker. **Read every draft before
posting it** — this tool drafts replies, it doesn't post them for you, and a human
should always review Reddit replies before they go out under anyone's account.

---

## Troubleshooting

- **`python` (or `claude`, or `pip`) is "not recognized"/"command not found"** — close
  the window completely and open a brand new one; installers need a fresh window to
  be picked up. Still broken on Windows — reinstall Python and make sure "Add to PATH"
  was checked.
- **`/reddit-tool` says it can't find the client / project folder** — Step 4
  (`python install_skill.py`) wasn't run from inside the actual `reddit-tool` folder,
  or wasn't run at all. Navigate into the folder (see Step 3) and re-run it.
- **Claude Code asks you to log in / says your plan doesn't have access** — this tool
  needs a paid Claude plan (Pro, Max, Team, or Enterprise), not a free account. See
  "What you'll need" above.
- **A client isn't listed when `/reddit-tool` asks which one to run** — its config
  file is missing from `reddit-tool/clients/`. Check that folder for a `<name>.json`
  file matching the client you expect.
- **Nothing in the drafts file / an empty list of threads** — that client's subreddits
  may simply have no relevant activity right now; try again later, or check
  `reddit-tool/clients/<name>.json`'s `subreddits` list is right for that client.

Anything else, contact **Alex Skinner** — the designated fallback for anything this guide doesn't cover.
