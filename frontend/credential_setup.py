"""First-run Reddit API credential setup.

Marketing Intelligence Studio needs a Reddit API key to run Reddit
Research. A non-technical user should never have to find, rename, or hand-edit
a `.env` file in a text editor to provide it — this module offers the same
two values (``REDDIT_CLIENT_ID`` / ``REDDIT_CLIENT_SECRET``) through a small
setup dialog instead, writing them to the same `.env` file `backend.config`
already reads (next to the app, or the repo root when running from source).
"""

from __future__ import annotations

import os
import tkinter as tk
import webbrowser
from collections.abc import Callable
from tkinter import messagebox

from backend.config import PROJECT_ROOT

REDDIT_APPS_URL = "https://www.reddit.com/prefs/apps"

_MANAGED_KEYS = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET")


def credentials_present() -> bool:
    """Whether Reddit credentials are already available in the environment."""
    return bool(os.environ.get("REDDIT_CLIENT_ID")) and bool(os.environ.get("REDDIT_CLIENT_SECRET"))


def save_reddit_credentials(client_id: str, client_secret: str) -> None:
    """Write the two Reddit credentials to `.env` and into the current
    process's environment, so Reddit Research works immediately — no restart
    needed.

    Every other line already in `.env` (MIS_ settings, a previously-set
    ``REDDIT_USER_AGENT``, etc.) is preserved untouched; only the two managed
    keys are replaced or appended.
    """
    env_path = PROJECT_ROOT / ".env"
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    kept = [line for line in lines if line.split("=", 1)[0].strip() not in _MANAGED_KEYS]
    kept.append(f"REDDIT_CLIENT_ID={client_id}")
    kept.append(f"REDDIT_CLIENT_SECRET={client_secret}")
    env_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    os.environ["REDDIT_CLIENT_ID"] = client_id
    os.environ["REDDIT_CLIENT_SECRET"] = client_secret


class RedditSetupDialog(tk.Toplevel):
    """Modal "Connect to Reddit" dialog shown whenever credentials are missing.

    ``on_saved`` is called (with no arguments) right after a successful save,
    so the caller can refresh anything that depends on credentials being
    present (e.g. re-enable a Run that was blocked).
    """

    def __init__(self, parent: tk.Tk, on_saved: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self._on_saved = on_saved
        self._show_secret = tk.BooleanVar(value=False)

        self.title("Connect to Reddit")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_skip)

        self._build_widgets()
        self.grab_set()
        self._center_on(parent)
        self._client_id_entry.focus_set()

    def _center_on(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        x, y = px + max((pw - w) // 2, 0), py + max((ph - h) // 2, 0)
        self.geometry(f"+{x}+{y}")

    def _build_widgets(self) -> None:
        tk.Label(
            self, text="Connect to Reddit", font=("TkDefaultFont", 13, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 4))

        tk.Label(
            self,
            text=(
                "Reddit Research needs a free Reddit API key to search Reddit.\n"
                "One-time setup, about 2 minutes. Ask your team lead if someone\n"
                "has already done this and can share the two values below."
            ),
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        tk.Button(
            self,
            text="Open reddit.com/prefs/apps to get your key  ↗",
            command=lambda: webbrowser.open(REDDIT_APPS_URL),
        ).pack(anchor="w", padx=20, pady=(0, 4))
        tk.Label(
            self,
            text='Click "create app", choose type "script", then copy the two values it gives you.',
            fg="#666666",
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        form = tk.Frame(self)
        form.pack(fill="x", padx=20)

        tk.Label(form, text="Client ID").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._client_id_entry = tk.Entry(form, width=42)
        self._client_id_entry.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 12))

        tk.Label(form, text="Secret").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self._secret_entry = tk.Entry(form, width=42, show="*")
        self._secret_entry.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 4))
        tk.Checkbutton(
            form, text="Show", variable=self._show_secret, command=self._toggle_secret_visibility
        ).grid(row=4, column=0, sticky="w", pady=(0, 12))

        self._error_var = tk.StringVar()
        tk.Label(self, textvariable=self._error_var, fg="#b00020").pack(
            anchor="w", padx=20, pady=(0, 4)
        )

        button_row = tk.Frame(self)
        button_row.pack(fill="x", padx=20, pady=(6, 20))
        tk.Button(button_row, text="Save and Continue", command=self._on_save, width=16).pack(
            side="right"
        )
        tk.Button(button_row, text="I'll do this later", command=self._on_skip).pack(
            side="right", padx=(0, 8)
        )

        self.bind("<Return>", lambda _event: self._on_save())

    def _toggle_secret_visibility(self) -> None:
        self._secret_entry.configure(show="" if self._show_secret.get() else "*")

    def _on_save(self) -> None:
        client_id = self._client_id_entry.get().strip()
        secret = self._secret_entry.get().strip()
        if not client_id or not secret:
            self._error_var.set("Both fields are required.")
            return

        try:
            save_reddit_credentials(client_id, secret)
        except OSError as exc:
            messagebox.showerror(
                "Couldn't save",
                f"Couldn't write the .env file next to the app:\n{exc}\n\n"
                "Ask whoever set up this folder to check its permissions.",
                parent=self,
            )
            return

        if self._on_saved is not None:
            self._on_saved()
        self.destroy()

    def _on_skip(self) -> None:
        self.destroy()
