import importlib.util
from pathlib import Path


def _load_install_skill():
    """install_skill.py lives at the reddit-tool project root, not under src/,
    so it isn't importable as a normal package module — load it by path."""
    module_path = Path(__file__).resolve().parent.parent / "install_skill.py"
    spec = importlib.util.spec_from_file_location("install_skill", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_replaces_every_placeholder_with_the_real_project_path(tmp_path, monkeypatch):
    install_skill = _load_install_skill()
    monkeypatch.setattr(install_skill, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(install_skill, "SKILL_SOURCE", tmp_path / "skill" / "SKILL.md")
    dest_dir = tmp_path / "home" / ".claude" / "skills" / "reddit-tool"
    monkeypatch.setattr(install_skill, "SKILL_DEST_DIR", dest_dir)
    monkeypatch.setattr(install_skill, "SKILL_DEST", dest_dir / "SKILL.md")

    (tmp_path / "skill").mkdir()
    (tmp_path / "skill" / "SKILL.md").write_text(
        "Project root: REDDIT_TOOL_PATH\nRun REDDIT_TOOL_PATH/scrape.py", encoding="utf-8"
    )

    install_skill.main()

    installed = (dest_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "REDDIT_TOOL_PATH" not in installed
    assert str(tmp_path) in installed
    assert installed.count(str(tmp_path)) == 2


def test_missing_skill_source_exits_with_error(tmp_path, monkeypatch, capsys):
    install_skill = _load_install_skill()
    monkeypatch.setattr(install_skill, "SKILL_SOURCE", tmp_path / "does-not-exist.md")

    try:
        install_skill.main()
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1

    assert "Couldn't find" in capsys.readouterr().out
