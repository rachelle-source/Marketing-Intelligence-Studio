import json
from pathlib import Path

from backend.reddit.client_context import load_client_context


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_loads_keywords_and_named_competitors(tmp_path: Path) -> None:
    client_dir = tmp_path / "kore"
    client_dir.mkdir()
    write_json(client_dir / "seo.json", {"primary_keywords": ["IoT connectivity", "enterprise IoT"]})
    write_json(
        client_dir / "competitors.json",
        {"named_competitors": [{"name": "Emnify", "type": "IoT connectivity provider"}]},
    )

    context = load_client_context(tmp_path, "kore")

    assert context.client_id == "kore"
    assert context.primary_keywords == ["IoT connectivity", "enterprise IoT"]
    assert context.competitor_names == ["Emnify"]


def test_loads_competing_concepts_and_organizations(tmp_path: Path) -> None:
    client_dir = tmp_path / "mcfie"
    client_dir.mkdir()
    write_json(client_dir / "seo.json", {"primary_keywords": []})
    write_json(
        client_dir / "competitors.json",
        {"competing_concepts_and_organizations": [{"name": "Bank on Yourself"}]},
    )

    context = load_client_context(tmp_path, "mcfie")
    assert context.competitor_names == ["Bank on Yourself"]


def test_missing_client_dir_returns_empty_context(tmp_path: Path) -> None:
    context = load_client_context(tmp_path, "does-not-exist")
    assert context.primary_keywords == []
    assert context.competitor_names == []


def test_invalid_json_is_ignored_not_raised(tmp_path: Path) -> None:
    client_dir = tmp_path / "broken"
    client_dir.mkdir()
    (client_dir / "seo.json").write_text("{not valid json", encoding="utf-8")

    context = load_client_context(tmp_path, "broken")
    assert context.primary_keywords == []
