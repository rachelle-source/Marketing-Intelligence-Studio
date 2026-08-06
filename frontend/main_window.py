"""The main desktop window.

Deliberately plain per this version's brief ("does not need to be beautiful
yet"): a client list, a tool list, a topic field (only used by tools that
need one), a Run button, and an output area. All business logic lives in
`RunController` / `client_discovery` / `tools` — this module only builds
widgets and wires their callbacks, per the "UI contains no business logic"
rule.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from frontend.client_discovery import ClientSummary
from frontend.run_controller import RunController, RunResult
from frontend.tools import ToolDefinition

WINDOW_TITLE = "Marketing Intelligence Studio"
WINDOW_SIZE = "780x520"


class MainWindow(tk.Tk):
    def __init__(
        self,
        clients: list[ClientSummary],
        tools: list[ToolDefinition],
        controller: RunController,
    ) -> None:
        super().__init__()
        self._clients = clients
        self._tools = tools
        self._controller = controller

        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)

        self._build_widgets()
        self._populate_lists()

    def _build_widgets(self) -> None:
        lists_frame = tk.Frame(self)
        lists_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        client_frame = tk.Frame(lists_frame)
        client_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(client_frame, text="Clients").pack(anchor="w")
        self._client_listbox = tk.Listbox(client_frame, exportselection=False)
        self._client_listbox.pack(fill="both", expand=True)

        tools_frame = tk.Frame(lists_frame)
        tools_frame.pack(side="left", fill="both", expand=True)
        tk.Label(tools_frame, text="Marketing Tools").pack(anchor="w")
        self._tool_listbox = tk.Listbox(tools_frame, exportselection=False)
        self._tool_listbox.pack(fill="both", expand=True)
        self._tool_listbox.bind("<<ListboxSelect>>", self._on_tool_selected)

        topic_frame = tk.Frame(self)
        topic_frame.pack(side="top", fill="x", padx=10)
        tk.Label(topic_frame, text="Topic:").pack(side="left")
        self._topic_var = tk.StringVar()
        self._topic_entry = tk.Entry(topic_frame, textvariable=self._topic_var)
        self._topic_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        run_frame = tk.Frame(self)
        run_frame.pack(side="top", fill="x", padx=10, pady=10)
        self._run_button = tk.Button(run_frame, text="Run", command=self._on_run_click, width=12)
        self._run_button.pack(side="left")
        self._status_var = tk.StringVar()
        tk.Label(run_frame, textvariable=self._status_var, anchor="w").pack(
            side="left", padx=(10, 0), fill="x", expand=True
        )

        output_frame = tk.Frame(self)
        output_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))
        tk.Label(output_frame, text="Output").pack(anchor="w")
        self._output_text = scrolledtext.ScrolledText(output_frame, height=10, state="disabled")
        self._output_text.pack(fill="both", expand=True)

    def _populate_lists(self) -> None:
        for client in self._clients:
            suffix = "" if client.status == "populated" else "  [no source data]"
            self._client_listbox.insert("end", f"{client.display_name}{suffix}")

        for tool in self._tools:
            suffix = "" if tool.available else "  [not available]"
            self._tool_listbox.insert("end", f"{tool.name}{suffix}")

        self._status_var.set(
            f"{len(self._clients)} client(s) discovered — "
            f"{sum(t.available for t in self._tools)}/{len(self._tools)} tool(s) available"
        )
        self._on_tool_selected()

    def _on_tool_selected(self, _event: object = None) -> None:
        tool = self._selected_tool()
        needs_topic = bool(tool and tool.requires_topic)
        self._topic_entry.configure(state="normal" if needs_topic else "disabled")

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
        client = self._selected_client()
        tool = self._selected_tool()
        topic = self._topic_var.get()
        result = self._controller.run(client, tool, topic)
        self._show_result(result)

    def _show_result(self, result: RunResult) -> None:
        prefix = "OK: " if result.success else "Not run: "
        self._output_text.configure(state="normal")
        self._output_text.delete("1.0", "end")
        self._output_text.insert("end", prefix + result.message)
        self._output_text.configure(state="disabled")
