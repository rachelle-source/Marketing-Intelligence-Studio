# Marketing Intelligence Studio — Version 1 Release

This folder contains everything needed to distribute Marketing Intelligence
Studio to a non-technical team member. Nothing in here requires Python,
Git, or a command line to use.

## What's in this folder

- **`HOW TO INSTALL.txt`** — step-by-step setup and launch instructions for
  non-technical users (also included inside each build zip below).
- **`MarketingIntelligenceStudio-Windows.zip`** and
  **`MarketingIntelligenceStudio-macOS.zip`** — see "Getting the built app"
  below. Once added to this folder: unzip, then double-click
  `Marketing Intelligence Studio.exe` (Windows) or
  `Marketing Intelligence Studio.app` (macOS) inside.

## Getting the built app

The real Windows `.exe` and macOS `.app` are built automatically by the
**Build Release** GitHub Actions workflow, from real Windows and macOS
runners. Download them from the latest successful workflow run and drop
the two zip files into this folder:

**Run:** https://github.com/rachelle-source/Marketing-Intelligence-Studio/actions/runs/31129138519

(If that run shows the macOS build still queued or cancelled — GitHub's
shared macOS runners are sometimes slow to become available — re-run the
workflow from the Actions tab, or check
https://github.com/rachelle-source/Marketing-Intelligence-Studio/actions/workflows/build-release.yml
for the most recent successful run.)

1. Open that link and sign in to GitHub if needed.
2. Scroll to the **Artifacts** section at the bottom of the run page.
3. Download `MarketingIntelligenceStudio-Windows` and
   `MarketingIntelligenceStudio-macOS`.
4. Rename each downloaded file to match the names above (GitHub appends
   `.zip` automatically) and place them in this `Release` folder.

Each zip is self-contained: the app itself, a `clients` folder with the
built-in client intelligence data, a `.env.example` file for Reddit API
credentials, the install instructions, and a `reddit-tool` folder (see
below). Nothing else needs to be downloaded or installed to run the main
app — the Python interpreter and all dependencies (including PRAW and
tkinter) are bundled inside it.

The `reddit-tool` folder is different: it's a separate, more advanced tool
(Reddit scraping + AI-drafted replies) that does need Python and
[Claude Code](https://claude.ai/code) installed separately, plus a paid
Claude plan. `reddit-tool/REDDIT_TOOL_SETUP.md` walks through that setup
from scratch. Its `clients/*.json` configs are pre-generated from the same
client intelligence as the main app, with a placeholder `notify_email`
each person replaces with their own (Step 5 of that guide) — nobody needs
Python or backend access just to get a config.

## Distributing to your team

1. Send the appropriate zip (Windows or macOS) to each team member, or share
   this whole `Release` folder via a shared drive.
2. Point them to `HOW TO INSTALL.txt` for the main app's setup.
3. One person should set up Reddit API credentials once (see the
   instructions) and can share the resulting `.env` file with the rest of
   the team so everyone doesn't need to create their own Reddit app.
4. **Alex Skinner is the designated fallback contact** for anything a
   teammate gets stuck on that these guides don't cover.
5. If your team will use the Reddit Reply Tool too, point them to
   `reddit-tool/REDDIT_TOOL_SETUP.md` inside the zip — that setup is
   per-person (each teammate needs their own Python + Claude Code install).

## Rebuilding this release

These builds are produced by the `Build Release` GitHub Actions workflow
(`.github/workflows/build-release.yml`), which runs PyInstaller on real
Windows and macOS runners (PyInstaller cannot cross-compile, so this can't
be built from a single machine). To produce a new release, run that
workflow (or push a `v*` tag) and download the resulting artifacts.

To build locally instead: `packaging/build_windows.bat` (on Windows) or
`packaging/build_macos.sh` (on macOS). See `packaging/pyinstaller.spec` for
the underlying build configuration.
