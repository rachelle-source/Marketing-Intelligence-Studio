import json
from pathlib import Path

from frontend.client_discovery import discover_clients


def write_profile(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_discovers_real_clients_directory() -> None:
    clients = discover_clients(Path(__file__).resolve().parent.parent / "clients")
    slugs = {c.slug for c in clients}
    assert "kore" in slugs
    assert "mcfie" in slugs
    kore = next(c for c in clients if c.slug == "kore")
    assert kore.display_name == "KORE Wireless"
    assert kore.status == "populated"


def test_skips_directories_without_profile_json(tmp_path: Path) -> None:
    (tmp_path / "no_profile").mkdir()
    (tmp_path / "no_profile" / "notes.txt").write_text("hi", encoding="utf-8")
    assert discover_clients(tmp_path) == []


def test_falls_back_to_slug_when_no_display_name(tmp_path: Path) -> None:
    client_dir = tmp_path / "acme"
    client_dir.mkdir()
    write_profile(client_dir / "profile.json", {"status": "no_source_data"})

    clients = discover_clients(tmp_path)
    assert clients[0].slug == "acme"
    assert clients[0].display_name == "acme"


def test_uses_company_when_client_name_missing(tmp_path: Path) -> None:
    client_dir = tmp_path / "acme"
    client_dir.mkdir()
    write_profile(client_dir / "profile.json", {"company": "Acme Corp"})

    clients = discover_clients(tmp_path)
    assert clients[0].display_name == "Acme Corp"


def test_invalid_json_is_skipped_not_raised(tmp_path: Path) -> None:
    client_dir = tmp_path / "broken"
    client_dir.mkdir()
    (client_dir / "profile.json").write_text("{not json", encoding="utf-8")

    assert discover_clients(tmp_path) == []


def test_missing_clients_dir_returns_empty_list(tmp_path: Path) -> None:
    assert discover_clients(tmp_path / "does-not-exist") == []


def test_sorted_by_display_name(tmp_path: Path) -> None:
    for slug, name in [("z", "Zeta"), ("a", "Alpha")]:
        d = tmp_path / slug
        d.mkdir()
        write_profile(d / "profile.json", {"client_name": name})

    clients = discover_clients(tmp_path)
    assert [c.display_name for c in clients] == ["Alpha", "Zeta"]
