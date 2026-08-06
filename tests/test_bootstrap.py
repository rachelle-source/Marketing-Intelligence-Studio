from pathlib import Path

from backend.config import AppConfig
from backend.core.bootstrap import initialize_app


def test_initialize_app_wires_everything_together(tmp_path: Path) -> None:
    config = AppConfig(
        _env_file=None,
        clients_dir=tmp_path / "clients",
        logs_dir=tmp_path / "logs",
        output_dir=tmp_path / "output",
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "app.db",
    )

    context = initialize_app(config)

    assert context.config is config
    assert (tmp_path / "logs" / "app.log").exists()
    assert context.database.db_path.exists()
    assert context.settings.all() == {}

    context.settings.set("theme", "dark")
    assert context.settings.get("theme") == "dark"
