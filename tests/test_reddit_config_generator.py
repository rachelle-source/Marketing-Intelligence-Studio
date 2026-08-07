import json
import sys
from pathlib import Path

import pytest

from backend.reddit.config_generator import (
    DEFAULT_MAX_THREADS,
    DEFAULT_NOTIFY_EMAIL,
    DEFAULT_SORT,
    ConfigGenerationError,
    generate_all,
    generate_client_config,
    write_client_config,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
REDDIT_TOOL_DIR = REPO_ROOT / "reddit-tool"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def make_client(
    clients_dir: Path,
    slug: str,
    *,
    profile: dict | None = None,
    seo: dict | None = None,
) -> None:
    client_dir = clients_dir / slug
    client_dir.mkdir(parents=True, exist_ok=True)
    write_json(client_dir / "profile.json", profile or {})
    write_json(client_dir / "seo.json", seo or {})


FULL_PROFILE = {
    "client_name": "Acme Corp",
    "description": "Acme Corp sells anvils to coyotes.",
    "reddit_config": {
        "subreddits": ["acmefans", "engineering"],
        "tone": "Deadpan, never sells directly.",
        "notify_email": "ops@acme.example.com",
        "max_threads": 20,
        "sort": "new",
    },
}
FULL_SEO = {"primary_keywords": ["anvils", "coyote traps"]}


def test_generate_client_config_uses_reddit_config_and_seo(tmp_path: Path) -> None:
    make_client(tmp_path, "acme", profile=FULL_PROFILE, seo=FULL_SEO)

    config = generate_client_config(tmp_path, "acme")

    assert config["client_name"] == "Acme Corp"
    assert config["subreddits"] == ["acmefans", "engineering"]
    assert config["keywords"] == ["anvils", "coyote traps"]
    assert config["brand_context"] == (
        "Acme Corp. Acme Corp sells anvils to coyotes. Tone: Deadpan, never sells directly."
    )
    assert config["notify_email"] == "ops@acme.example.com"
    assert config["max_threads"] == 20
    assert config["sort"] == "new"


def test_defaults_apply_when_reddit_config_omits_them(tmp_path: Path) -> None:
    profile = {
        "client_name": "Acme Corp",
        "description": "Acme Corp sells anvils to coyotes.",
        "reddit_config": {"subreddits": ["acmefans"]},
    }
    make_client(tmp_path, "acme", profile=profile, seo=FULL_SEO)

    config = generate_client_config(tmp_path, "acme")

    assert config["notify_email"] == DEFAULT_NOTIFY_EMAIL
    assert config["max_threads"] == DEFAULT_MAX_THREADS
    assert config["sort"] == DEFAULT_SORT


def test_company_field_used_when_client_name_missing(tmp_path: Path) -> None:
    profile = {
        "company": "Acme Corp",
        "core_promise": "Anvils, fast.",
        "reddit_config": {"subreddits": ["acmefans"]},
    }
    make_client(tmp_path, "acme", profile=profile, seo=FULL_SEO)

    config = generate_client_config(tmp_path, "acme")
    assert config["client_name"] == "Acme Corp"
    assert config["brand_context"] == "Acme Corp. Anvils, fast."


@pytest.mark.parametrize(
    "profile,seo,expected_message",
    [
        ({}, FULL_SEO, "no client_name or company"),
        ({"client_name": "Acme"}, FULL_SEO, "no reddit_config.subreddits"),
        (
            {"client_name": "Acme", "reddit_config": {"subreddits": ["x"]}},
            {},
            "no primary_keywords",
        ),
        (
            {
                "client_name": "Acme",
                "description": "Acme.",
                "reddit_config": {"subreddits": ["x"], "sort": "relevance"},
            },
            FULL_SEO,
            "sort must be one of",
        ),
    ],
)
def test_generate_raises_for_missing_required_knowledge(
    tmp_path: Path, profile: dict, seo: dict, expected_message: str
) -> None:
    make_client(tmp_path, "acme", profile=profile, seo=seo)

    with pytest.raises(ConfigGenerationError, match=expected_message):
        generate_client_config(tmp_path, "acme")


def test_brand_context_falls_back_to_client_name_alone(tmp_path: Path) -> None:
    profile = {"client_name": "Acme", "reddit_config": {"subreddits": ["x"]}}
    make_client(tmp_path, "acme", profile=profile, seo=FULL_SEO)

    config = generate_client_config(tmp_path, "acme")
    assert config["brand_context"] == "Acme."


def test_missing_profile_json_raises(tmp_path: Path) -> None:
    (tmp_path / "acme").mkdir()
    with pytest.raises(ConfigGenerationError, match="No profile.json"):
        generate_client_config(tmp_path, "acme")


def test_write_client_config_writes_valid_json(tmp_path: Path) -> None:
    make_client(tmp_path, "acme", profile=FULL_PROFILE, seo=FULL_SEO)
    out_dir = tmp_path / "reddit-tool-clients"

    out_path = write_client_config(tmp_path, "acme", out_dir)

    assert out_path == out_dir / "acme.json"
    assert json.loads(out_path.read_text(encoding="utf-8"))["client_name"] == "Acme Corp"


def test_generate_all_skips_unbuildable_clients_and_reports_errors(tmp_path: Path) -> None:
    make_client(tmp_path, "acme", profile=FULL_PROFILE, seo=FULL_SEO)
    make_client(tmp_path, "scaffold", profile={"client_name": None}, seo={})
    out_dir = tmp_path / "reddit-tool-clients"

    results = generate_all(tmp_path, out_dir)

    assert results["acme"] == out_dir / "acme.json"
    assert isinstance(results["scaffold"], ConfigGenerationError)
    assert (out_dir / "acme.json").is_file()
    assert not (out_dir / "scaffold.json").exists()


# --- Integration: validate against the real, vendored reddit-tool's own loader ---


@pytest.fixture()
def reddit_tool_load_config():
    """Import reddit-tool's real src.config.load_config for one test, then
    remove it and any src.* modules from sys.modules so this vendored
    project's "src" package doesn't leak into other tests.
    """
    if not REDDIT_TOOL_DIR.is_dir():
        pytest.skip("reddit-tool/ is not vendored into this checkout")

    sys.path.insert(0, str(REDDIT_TOOL_DIR))
    stale_modules = {name: mod for name, mod in sys.modules.items() if name == "src" or name.startswith("src.")}
    for name in stale_modules:
        del sys.modules[name]
    try:
        from src.config import load_config

        yield load_config
    finally:
        sys.path.remove(str(REDDIT_TOOL_DIR))
        for name in list(sys.modules):
            if name == "src" or name.startswith("src."):
                del sys.modules[name]


@pytest.mark.parametrize("slug", ["kore", "korr", "8msolar", "mcfie"])
def test_generated_config_passes_real_reddit_tool_validation(
    tmp_path: Path, reddit_tool_load_config, slug: str
) -> None:
    clients_dir = REPO_ROOT / "clients"
    out_path = write_client_config(clients_dir, slug, tmp_path)

    client_config = reddit_tool_load_config(str(out_path))

    assert client_config.client_name
    assert client_config.subreddits
    assert client_config.keywords
    assert client_config.brand_context
    assert client_config.notify_email
    assert client_config.max_threads > 0
    assert client_config.sort in {"hot", "new", "top"}
