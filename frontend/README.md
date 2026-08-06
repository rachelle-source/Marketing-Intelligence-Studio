# Frontend (v3 — tuned so it's obvious what to do)

```bash
python -m frontend.app
```

A Tkinter window showing a client list (discovered from `clients/`), a
marketing tool list, a topic field, and a Run button. It does not need to
be beautiful — it needs a first-time user to never wonder what to click.

- `client_discovery.py` — reads `clients/<slug>/profile.json`
- `tools.py` — the fixed marketing tool registry
- `run_controller.py` — wires `(client, tool, topic)` to real backend calls;
  no `tkinter` import, fully unit-testable on its own. `RunResult` includes
  `saved_to` (where the report landed) and `needs_focus` (which control to
  return keyboard focus to on failure).
- `main_window.py` — the actual window; thin, Tk-only, no business logic.
  Run executes on a background thread (network calls would otherwise freeze
  the window) with results delivered via a thread-safe queue polled through
  `after()`. Reddit Research is pre-selected on launch, the topic field
  shows example placeholder text, the output pane opens with numbered
  instructions instead of a blank box, and the report renders as formatted
  text (bold/headings/bullets) rather than raw Markdown syntax.
- `app.py` — entrypoint; wires `backend.core.bootstrap` + `RedditService`

Only **Reddit Research** is wired to a real backend call
(`backend.reddit.RedditService`) today. The other three tools stay listed
in grey (not hidden) so the team can see the roadmap, but Run reports
plainly that they're not implemented yet. When Reddit Research runs, the
output pane shows the *full* rendered report, the status bar confirms
where it was saved and how long it took, and focus returns to the topic
field (with the old topic selected) so the next search is one keystroke
away.

## Testing

`tkinter` is stdlib but needs the system Tk package (`python3-tk` on
Debian/Ubuntu; bundled by default on Windows/macOS Python installers).
Headless test runs (no physical display) need a virtual display server:

```bash
xvfb-run -a pytest tests/test_main_window.py
```

`tests/test_main_window.py` skips itself automatically if no display is
available at all.

## Future direction (Design Pack)

- Desktop-first, dark mode by default, light mode supported
- Layout: left navigation, top toolbar, main workspace, right context panel
  (future), bottom status bar
- Primary navigation: Dashboard, Clients, Research, AI Writer, Knowledge,
  Exports, Settings
- The UI must never call external APIs or the database directly — only
  through `backend.services` interfaces (already true today: the window
  only ever calls `RunController`)

Packaging direction from the Engineering Pack: PyInstaller first
(Windows `.exe` / macOS `.app`), with Tauri as a future evaluation.
