"""One-time setup: installs the Claude Code skill (skill/SKILL.md) to
~/.claude/skills/reddit-tool/SKILL.md, with every REDDIT_TOOL_PATH placeholder
automatically replaced with this reddit-tool folder's real location.

Run this once per computer, from inside the reddit-tool folder:

    python install_skill.py

No arguments needed — the script finds its own folder and uses that as the
path to substitute, so there's nothing to type or copy-paste by hand.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SKILL_SOURCE = PROJECT_ROOT / "skill" / "SKILL.md"
SKILL_DEST_DIR = Path.home() / ".claude" / "skills" / "reddit-tool"
SKILL_DEST = SKILL_DEST_DIR / "SKILL.md"


def main() -> None:
    if not SKILL_SOURCE.is_file():
        print(f"Couldn't find {SKILL_SOURCE} — run this script from inside the reddit-tool folder.")
        raise SystemExit(1)

    text = SKILL_SOURCE.read_text(encoding="utf-8")
    replaced = text.replace("REDDIT_TOOL_PATH", str(PROJECT_ROOT))

    SKILL_DEST_DIR.mkdir(parents=True, exist_ok=True)
    SKILL_DEST.write_text(replaced, encoding="utf-8")

    print("Done! The reddit-tool skill is installed.")
    print(f"  Project folder used: {PROJECT_ROOT}")
    print(f"  Skill installed to:  {SKILL_DEST}")
    print()
    print("Next: open Claude Code in any folder and type /reddit-tool")


if __name__ == "__main__":
    main()
