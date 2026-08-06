"""Desktop app entrypoint.

Wires config + logging + database (via `backend.core.bootstrap`), discovers
clients, builds the tool registry, constructs the one real service
(`RedditService`), and launches the main window.

Run with:

    python -m frontend.app
"""

from __future__ import annotations

import logging

from backend.core.bootstrap import initialize_app
from backend.reddit.service import RedditService
from frontend.client_discovery import discover_clients
from frontend.main_window import MainWindow
from frontend.run_controller import RunController
from frontend.tools import list_marketing_tools

logger = logging.getLogger(__name__)


def main() -> None:
    context = initialize_app()

    clients = discover_clients(context.config.clients_dir)
    tools = list_marketing_tools()

    reddit_service = RedditService(database=context.database, clients_dir=context.config.clients_dir)
    controller = RunController(reddit_service=reddit_service)

    logger.info("Launching desktop UI with %d client(s), %d tool(s)", len(clients), len(tools))
    window = MainWindow(clients=clients, tools=tools, controller=controller)
    window.mainloop()


if __name__ == "__main__":
    main()
