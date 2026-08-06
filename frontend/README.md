# Frontend (TODO — not built yet)

This package intentionally contains no code yet. Per the current project
phase, only the backend foundation (config, logging, database, service
interfaces) is being built; the desktop GUI is a separate, later step.

When it is built, it should follow the Design Pack's UI Guidelines:

- Desktop-first, dark mode by default, light mode supported.
- Layout: left navigation, top toolbar, main workspace, right context panel
  (future), bottom status bar.
- Primary navigation: Dashboard, Clients, Research, AI Writer, Knowledge,
  Exports, Settings.
- The UI must never call external APIs or the database directly — only
  through `backend.services` interfaces.

Packaging direction from the Engineering Pack: PyInstaller first
(Windows `.exe` / macOS `.app`), with Tauri as a future evaluation.

TODO: Desktop GUI implementation.
