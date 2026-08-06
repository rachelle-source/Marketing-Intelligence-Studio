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

**Run:** https://github.com/rachelle-source/Marketing-Intelligence-Studio/actions/runs/31129087130

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
credentials, and the install instructions. Nothing else needs to be
downloaded or installed — the Python interpreter and all dependencies
(including PRAW and tkinter) are bundled inside the app.

## Distributing to your team

1. Send the appropriate zip (Windows or macOS) to each team member, or share
   this whole `Release` folder via a shared drive.
2. Point them to `HOW TO INSTALL.txt` for setup.
3. One person should set up Reddit API credentials once (see the
   instructions) and can share the resulting `.env` file with the rest of
   the team so everyone doesn't need to create their own Reddit app.

## Rebuilding this release

These builds are produced by the `Build Release` GitHub Actions workflow
(`.github/workflows/build-release.yml`), which runs PyInstaller on real
Windows and macOS runners (PyInstaller cannot cross-compile, so this can't
be built from a single machine). To produce a new release, run that
workflow (or push a `v*` tag) and download the resulting artifacts.

To build locally instead: `packaging/build_windows.bat` (on Windows) or
`packaging/build_macos.sh` (on macOS). See `packaging/pyinstaller.spec` for
the underlying build configuration.
