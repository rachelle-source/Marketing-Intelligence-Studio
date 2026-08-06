"""The main desktop window.

Deliberately plain per this version's brief ("does not need to be beautiful
yet") but tuned so the one working workflow — Reddit Research — takes as
little effort as possible to discover and run: pick a client, type a topic,
press Run (or Enter). All business logic lives in `RunController` /
`client_discovery` / `tools` — this module only builds widgets and wires
their callbacks, per the "UI contains no business logic" rule.

Reddit Research hits the network and can take a few seconds, so Run runs it
on a background thread rather than the Tk main thread — otherwise the whole
window would freeze (no redraw, "Not Responding" on Windows) for the
duration of every search. Results come back through a thread-safe queue,
polled from the main thread via `after()`, which is the standard safe way to
touch Tk widgets from a background thread's result.

The intended handoff to NotebookLM (the team's long-term knowledge base) is:

    Research -> Save for NotebookLM -> Drag into NotebookLM -> Done.

So the three buttons below the report (Save for NotebookLM / Open Export
Folder / Copy Report) all act on "the report currently on screen" and stay
disabled until there is one.
"""

from __future__ import annotations

import queue
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

from backend.config import PROJECT_ROOT
from backend.reddit.export import export_report_markdown
from frontend.client_discovery import ClientSummary
from frontend.credential_setup import RedditSetupDialog, credentials_present
from frontend.os_actions import open_in_file_manager
from frontend.run_controller import RunController, RunResult
from frontend.tools import ToolDefinition

WINDOW_TITLE = "Marketing Intelligence Studio"
WINDOW_SIZE = "900x720"
QUEUE_POLL_INTERVAL_MS = 100
DIMMED_COLOR = "#999999"

TOPIC_PLACEHOLDER = 'e.g. "pricing", "reliability", "customer support"'

WELCOME_MESSAGE = (
    "Welcome. Here's how to run your first Reddit Research report:\n\n"
    "1. Pick a client from the list on the left.\n"
    '2. Type a topic above — try "pricing" or "reliability".\n'
    "3. Click Run, or just press Enter.\n\n"
    "The report will appear here, and is saved automatically to that "
    "client's knowledge base for next time.\n\n"
    "When it's ready, use Save for NotebookLM to export a clean copy for "
    "the team's knowledge base, or Copy Report to paste it elsewhere."
)

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _windows_icon_path() -> Path | None:
    """Where to find the bundled Windows icon at runtime, if any.

    Only meaningful on Windows: Tk's ``iconbitmap`` only accepts the .ico
    format, so this is a deliberate no-op on macOS/Linux, both of which
    raise ``TclError`` for it (caught by the caller) — macOS gets its dock
    icon from the .app bundle itself (see packaging/pyinstaller.spec)
    instead, and Tk windows there don't show a title-bar icon at all.
    """
    base = Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "frozen", False) else PROJECT_ROOT
    candidate = base / "packaging" / "assets" / "icon.ico"
    return candidate if candidate.exists() else None


class MainWindow(tk.Tk):
    def __init__(
        self,
        clients: list[ClientSummary],
        tools: list[ToolDefinition],
        controller: RunController,
        output_dir: Path,
        check_credentials: bool = True,
    ) -> None:
        super().__init__()
        self._clients = clients
        self._tools = tools
        self._controller = controller
        self._output_dir = output_dir
        self._base_status = ""
        self._running = False
        self._result_queue: queue.Queue[RunResult] = queue.Queue()
        self._last_thread: threading.Thread | None = None
        self._poll_job: str | None = None
        self._topic_placeholder_active = False

        # The report currently on screen, for the export/copy buttons.
        self._last_client: ClientSummary | None = None
        self._last_topic: str | None = None
        self._last_report_markdown: str | None = None

        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(760, 560)
        self._set_window_icon()

        self._build_menu()
        self._build_widgets()
        self._populate_lists()
        if check_credentials:
            self._maybe_show_credential_setup()

    def _set_window_icon(self) -> None:
        icon_path = _windows_icon_path()
        if icon_path is None:
            return
        try:
            self.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass  # e.g. running on Linux/macOS, where Tk can't load .ico

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)
        settings_menu = tk.Menu(menu_bar, tearoff=False)
        settings_menu.add_command(label="Reddit API Setup...", command=self._open_credential_setup_dialog)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.configure(menu=menu_bar)

    def _maybe_show_credential_setup(self) -> None:
        if not credentials_present():
            self._open_credential_setup_dialog()

    def _open_credential_setup_dialog(self) -> None:
        RedditSetupDialog(self, on_saved=self._on_credentials_saved)

    def _on_credentials_saved(self) -> None:
        self._status_var.set(f"{self._base_status} — Reddit connected. You're ready to run a search.")

    def _build_widgets(self) -> None:
        lists_frame = tk.Frame(self)
        lists_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))

        client_frame = tk.Frame(lists_frame)
        client_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(client_frame, text="1. Pick a client").pack(anchor="w")
        self._client_listbox = tk.Listbox(client_frame, exportselection=False)
        self._client_listbox.pack(fill="both", expand=True)

        tools_frame = tk.Frame(lists_frame)
        tools_frame.pack(side="left", fill="both", expand=True)
        tk.Label(tools_frame, text="Marketing tools").pack(anchor="w")
        self._tool_listbox = tk.Listbox(tools_frame, exportselection=False)
        self._tool_listbox.pack(fill="both", expand=True)
        self._tool_listbox.bind("<<ListboxSelect>>", self._on_tool_selected)

        topic_frame = tk.Frame(self)
        topic_frame.pack(side="top", fill="x", padx=10, pady=(8, 0))
        tk.Label(topic_frame, text="2. Type a topic").pack(anchor="w")
        self._topic_entry = tk.Entry(topic_frame)
        self._topic_entry.pack(fill="x")
        self._topic_default_fg = self._topic_entry.cget("fg")
        self._topic_entry.bind("<Return>", lambda _event: self._on_run_click())
        self._topic_entry.bind("<FocusIn>", self._on_topic_focus_in)
        self._topic_entry.bind("<FocusOut>", self._on_topic_focus_out)

        run_frame = tk.Frame(self)
        run_frame.pack(side="top", fill="x", padx=10, pady=10)
        self._run_button = tk.Button(
            run_frame, text="3. Run", command=self._on_run_click, width=12
        )
        self._run_button.pack(side="left")
        tk.Label(run_frame, text="(or press Enter)", fg=DIMMED_COLOR).pack(side="left", padx=(6, 0))
        self._status_var = tk.StringVar()
        tk.Label(run_frame, textvariable=self._status_var, anchor="w").pack(
            side="left", padx=(10, 0), fill="x", expand=True
        )

        output_frame = tk.Frame(self)
        output_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 6))
        tk.Label(output_frame, text="Report").pack(anchor="w")
        self._output_text = scrolledtext.ScrolledText(output_frame, height=18, state="disabled", wrap="word")
        self._output_text.pack(fill="both", expand=True)
        self._configure_report_tags()

        export_frame = tk.Frame(self)
        export_frame.pack(side="top", fill="x", padx=10, pady=(0, 10))
        self._save_button = tk.Button(
            export_frame,
            text="Save for NotebookLM",
            command=self._on_save_for_notebooklm_click,
            state="disabled",
        )
        self._save_button.pack(side="left")
        self._open_folder_button = tk.Button(
            export_frame,
            text="Open Export Folder",
            command=self._on_open_export_folder_click,
            state="disabled",
        )
        self._open_folder_button.pack(side="left", padx=(6, 0))
        self._copy_button = tk.Button(
            export_frame,
            text="Copy Report",
            command=self._on_copy_report_click,
            state="disabled",
        )
        self._copy_button.pack(side="left", padx=(6, 0))

    def _configure_report_tags(self) -> None:
        self._output_text.tag_configure("h2", font=("TkDefaultFont", 14, "bold"), spacing3=8)
        self._output_text.tag_configure("h3", font=("TkDefaultFont", 12, "bold"), spacing1=10, spacing3=4)
        self._output_text.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
        self._output_text.tag_configure("italic", font=("TkDefaultFont", 9, "italic"), foreground="#666666")
        self._output_text.tag_configure("body", font=("TkDefaultFont", 10))

    def _populate_lists(self) -> None:
        for client in self._clients:
            suffix = "" if client.status == "populated" else "  (profile not set up yet)"
            self._client_listbox.insert("end", f"{client.display_name}{suffix}")

        for index, tool in enumerate(self._tools):
            suffix = "" if tool.available else "  (coming soon)"
            self._tool_listbox.insert("end", f"{tool.name}{suffix}")
            if not tool.available:
                self._tool_listbox.itemconfig(index, fg=DIMMED_COLOR)

        available_tool_index = next((i for i, t in enumerate(self._tools) if t.available), None)
        if available_tool_index is not None:
            self._tool_listbox.selection_set(available_tool_index)
            available_tool = self._tools[available_tool_index]
            self._base_status = f"{len(self._clients)} client(s) ready · {available_tool.name} is ready to run"
        else:
            self._base_status = f"{len(self._clients)} client(s) ready"

        self._status_var.set(self._base_status)
        self._on_tool_selected()
        self._set_output_text(WELCOME_MESSAGE)
        self._client_listbox.focus_set()

    def _on_tool_selected(self, _event: object = None) -> None:
        tool = self._selected_tool()
        needs_topic = bool(tool and tool.requires_topic)
        if needs_topic:
            self._topic_entry.configure(state="normal")
            if not self._topic_entry.get():
                self._show_topic_placeholder()
        else:
            self._topic_entry.configure(state="disabled")

    def _show_topic_placeholder(self) -> None:
        self._topic_entry.delete(0, "end")
        self._topic_entry.insert(0, TOPIC_PLACEHOLDER)
        self._topic_entry.configure(fg=DIMMED_COLOR)
        self._topic_placeholder_active = True

    def _on_topic_focus_in(self, _event: object) -> None:
        if self._topic_placeholder_active:
            self._topic_entry.delete(0, "end")
            self._topic_entry.configure(fg=self._topic_default_fg)
            self._topic_placeholder_active = False

    def _on_topic_focus_out(self, _event: object) -> None:
        if not self._topic_entry.get().strip():
            self._show_topic_placeholder()

    def _topic_text(self) -> str:
        if self._topic_placeholder_active:
            return ""
        return self._topic_entry.get()

    def _selected_client(self) -> ClientSummary | None:
        selection = self._client_listbox.curselection()
        if not selection:
            return None
        return self._clients[selection[0]]

    def _selected_tool(self) -> ToolDefinition | None:
        selection = self._tool_listbox.curselection()
        if not selection:
            return None
        return self._tools[selection[0]]

    def _on_run_click(self) -> None:
        if self._running:
            return  # ignore double-clicks / repeated Enter while a run is in flight

        client = self._selected_client()
        tool = self._selected_tool()
        topic = self._topic_text()

        self._running = True
        self._run_button.configure(state="disabled")
        self._set_export_buttons_state("disabled")
        self._status_var.set(f"{self._base_status} — Running…")
        self._set_output_text("Running Reddit research — this can take a few seconds…")

        self._last_thread = threading.Thread(
            target=self._run_in_background, args=(client, tool, topic), daemon=True
        )
        self._last_thread.start()
        self._poll_job = self.after(QUEUE_POLL_INTERVAL_MS, self._poll_result_queue)

    def _run_in_background(
        self, client: ClientSummary | None, tool: ToolDefinition | None, topic: str
    ) -> None:
        # Runs on a worker thread — must not touch any Tk widget directly.
        result = self._controller.run(client, tool, topic)
        self._result_queue.put(result)

    def _poll_result_queue(self) -> None:
        try:
            result = self._result_queue.get_nowait()
        except queue.Empty:
            self._poll_job = self.after(QUEUE_POLL_INTERVAL_MS, self._poll_result_queue)
            return
        self._poll_job = None
        self._running = False
        self._run_button.configure(state="normal")
        self._show_result(result)

    def _show_result(self, result: RunResult) -> None:
        if result.duration_seconds is not None:
            status = "Completed" if result.success else "Not run"
            saved_note = f" — saved to {result.saved_to}" if result.saved_to else ""
            self._status_var.set(f"{self._base_status} — {status} in {result.duration_seconds:.1f}s{saved_note}")
        else:
            self._status_var.set(self._base_status)

        self._set_output_text(result.message)

        if result.success:
            self._last_client = self._selected_client()
            self._last_topic = self._topic_text().strip()
            self._last_report_markdown = result.message
            self._set_export_buttons_state("normal")
            self._ready_topic_for_next_run()
        else:
            self._set_export_buttons_state("disabled")
            if result.credentials_missing:
                self._open_credential_setup_dialog()
            elif result.needs_focus == "client":
                self._client_listbox.focus_set()
            elif result.needs_focus == "topic":
                self._topic_entry.focus_set()

    def _set_export_buttons_state(self, state: str) -> None:
        self._save_button.configure(state=state)
        self._open_folder_button.configure(state=state)
        self._copy_button.configure(state=state)

    def _ready_topic_for_next_run(self) -> None:
        """After a successful run, put the cursor back in the topic field
        with the old topic selected — so typing a new one and hitting
        Enter immediately starts the next search.
        """
        if str(self._topic_entry["state"]) != "normal":
            return
        self._topic_entry.focus_set()
        self._topic_entry.selection_range(0, "end")

    def _on_save_for_notebooklm_click(self) -> None:
        if not self._last_client or not self._last_report_markdown:
            return
        path = export_report_markdown(
            self._output_dir, self._last_client.slug, self._last_topic or "topic", self._last_report_markdown
        )
        short_path = "/".join(path.parts[-3:])
        self._status_var.set(f"{self._base_status} — Saved for NotebookLM: {short_path}")

    def _on_open_export_folder_click(self) -> None:
        if not self._last_client:
            return
        folder = self._output_dir / self._last_client.slug
        open_in_file_manager(folder)
        self._status_var.set(f"{self._base_status} — Opened {self._last_client.slug}/ in your file manager")

    def _on_copy_report_click(self) -> None:
        if not self._last_report_markdown:
            return
        self.clipboard_clear()
        self.clipboard_append(self._last_report_markdown)
        self._status_var.set(f"{self._base_status} — Report copied to clipboard")

    def _set_output_text(self, text: str) -> None:
        self._output_text.configure(state="normal")
        self._output_text.delete("1.0", "end")
        self._insert_formatted(text)
        self._output_text.configure(state="disabled")

    def _insert_formatted(self, markdown_text: str) -> None:
        """Render the lightweight Markdown the report/messages use as
        actual formatted text — bold, headings, bullets — instead of
        showing literal '##' and '**' characters.
        """
        for raw_line in markdown_text.split("\n"):
            line = raw_line.rstrip()
            if line.strip() == "---":
                continue
            if line.startswith("### "):
                self._output_text.insert("end", line[4:] + "\n", ("h3",))
                continue
            if line.startswith("## "):
                self._output_text.insert("end", line[3:] + "\n", ("h2",))
                continue
            if len(line) > 1 and line.startswith("_") and line.endswith("_"):
                self._output_text.insert("end", line.strip("_") + "\n", ("italic",))
                continue

            line = _LINK_RE.sub(lambda m: f"{m.group(1)} ({m.group(2)})", line)
            if line.startswith("- "):
                line = "• " + line[2:]
            self._insert_inline_bold(line + "\n")

    def _insert_inline_bold(self, line: str) -> None:
        pos = 0
        for match in _BOLD_RE.finditer(line):
            self._output_text.insert("end", line[pos : match.start()], ("body",))
            self._output_text.insert("end", match.group(1), ("body", "bold"))
            pos = match.end()
        self._output_text.insert("end", line[pos:], ("body",))

    def destroy(self) -> None:
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except tk.TclError:
                pass
            self._poll_job = None
        super().destroy()
