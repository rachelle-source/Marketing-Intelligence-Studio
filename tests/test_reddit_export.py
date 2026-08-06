from datetime import date
from pathlib import Path

from backend.reddit.export import build_export_filename, export_report_markdown, slugify


def test_slugify_lowercases_and_hyphenates() -> None:
    assert slugify("IoT Connectivity Pricing") == "iot-connectivity-pricing"


def test_slugify_strips_punctuation() -> None:
    assert slugify("What's the deal with eSIM?!") == "what-s-the-deal-with-esim"


def test_slugify_collapses_repeated_separators() -> None:
    assert slugify("pricing   &   reliability") == "pricing-reliability"


def test_slugify_caps_length() -> None:
    long_topic = "a " * 80
    slug = slugify(long_topic)
    assert len(slug) <= 60
    assert not slug.endswith("-")


def test_slugify_empty_topic_has_fallback() -> None:
    assert slugify("   ") == "topic"


def test_build_export_filename_uses_date_then_topic() -> None:
    filename = build_export_filename("Pricing", date(2026, 8, 6))
    assert filename == "2026-08-06_pricing.md"


def test_export_report_markdown_writes_under_client_folder(tmp_path: Path) -> None:
    path = export_report_markdown(
        tmp_path, "kore", "IoT connectivity pricing", "## Reddit Research Brief — \"pricing\"\n\nbody",
        on=date(2026, 8, 6),
    )
    assert path == tmp_path / "kore" / "2026-08-06_iot-connectivity-pricing.md"
    assert path.is_file()


def test_export_promotes_h2_to_h1_for_standalone_file(tmp_path: Path) -> None:
    path = export_report_markdown(
        tmp_path, "kore", "pricing", "## Reddit Research Brief — \"pricing\"\n\nbody", on=date(2026, 8, 6)
    )
    content = path.read_text(encoding="utf-8")
    assert content.startswith("# Reddit Research Brief")
    assert "## Reddit Research Brief" not in content


def test_export_creates_client_folder_if_missing(tmp_path: Path) -> None:
    export_report_markdown(tmp_path, "brand-new-client", "topic", "## Title\n\nbody", on=date(2026, 1, 1))
    assert (tmp_path / "brand-new-client").is_dir()


def test_export_overwrites_same_client_topic_day(tmp_path: Path) -> None:
    on = date(2026, 8, 6)
    path1 = export_report_markdown(tmp_path, "kore", "pricing", "## Title\n\nfirst version", on=on)
    path2 = export_report_markdown(tmp_path, "kore", "pricing", "## Title\n\nsecond version", on=on)

    assert path1 == path2
    content = path2.read_text(encoding="utf-8")
    assert "second version" in content
    assert "first version" not in content


def test_export_defaults_to_today_when_no_date_given(tmp_path: Path) -> None:
    path = export_report_markdown(tmp_path, "kore", "pricing", "## Title\n\nbody")
    assert path.parent == tmp_path / "kore"
    assert path.name.endswith("_pricing.md")
