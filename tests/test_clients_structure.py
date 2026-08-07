import json
from pathlib import Path

import pytest

CLIENTS_DIR = Path(__file__).resolve().parent.parent / "clients"

EXPECTED_SLUGS = {
    "kore",
    "korr",
    "8msolar",
    "mcfie",
    "solartime",
    "crinkletime",
    "unsexy_businessmen",
}

JSON_FILES = ["profile.json", "prompts.json", "seo.json", "competitors.json"]

KNOWLEDGE_FILES = [
    "faq.md",
    "objections.md",
    "messaging.md",
    "terminology.md",
    "products.md",
    "blog_topics.md",
    "research.md",
    "reddit.md",
]

POPULATED_SLUGS = {"kore", "mcfie", "korr", "8msolar"}


def client_dirs() -> list[Path]:
    return [p for p in CLIENTS_DIR.iterdir() if p.is_dir()]


def test_all_expected_client_dirs_exist() -> None:
    found = {p.name for p in client_dirs()}
    assert EXPECTED_SLUGS.issubset(found)


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_client_has_all_json_files(slug: str) -> None:
    for filename in JSON_FILES:
        path = CLIENTS_DIR / slug / filename
        assert path.is_file(), f"missing {path}"
        json.loads(path.read_text(encoding="utf-8"))  # must parse


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_client_has_all_knowledge_files(slug: str) -> None:
    for filename in KNOWLEDGE_FILES:
        path = CLIENTS_DIR / slug / "knowledge" / filename
        assert path.is_file(), f"missing {path}"
        assert path.read_text(encoding="utf-8").strip(), f"empty {path}"


@pytest.mark.parametrize("slug", sorted(POPULATED_SLUGS))
def test_populated_clients_have_populated_status(slug: str) -> None:
    for filename in JSON_FILES:
        data = json.loads((CLIENTS_DIR / slug / filename).read_text(encoding="utf-8"))
        assert data["status"] == "populated"
        assert data["source"], f"{slug}/{filename} missing a source citation"


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS - POPULATED_SLUGS))
def test_scaffold_clients_have_no_source_data_status(slug: str) -> None:
    for filename in JSON_FILES:
        data = json.loads((CLIENTS_DIR / slug / filename).read_text(encoding="utf-8"))
        assert data["status"] == "no_source_data"
        assert data["source"] is None
