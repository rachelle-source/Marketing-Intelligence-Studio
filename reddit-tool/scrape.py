"""
Standalone Reddit scraper for Keystone Reddit tool.
Outputs thread data to stdout — paste the output into Claude Code, then run the relevant skill.
No API key required.

Usage (from reddit-tool/ directory):
    python scrape.py --client 8msolar
    python scrape.py --client solartime-usa
    python scrape.py --client mcfie-insurance
    python scrape.py --client korr
    python scrape.py --all
"""

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from src.config import load_config, ConfigError
from src.scraper import fetch_all_threads


# Force stdout to UTF-8 so em dashes and other Unicode chars from Reddit
# don't crash on Windows terminals (cp1252 default).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, TypeError):
    # Older Python versions or non-reconfigurable streams — fall through.
    pass

CLIENTS_DIR = Path(__file__).parent / "clients"


def list_client_slugs() -> list[str]:
    return sorted(
        f.stem for f in CLIENTS_DIR.glob("*.json") if not f.stem.startswith("_")
    )


def scrape_one(slug: str, json_out: str | None = None) -> None:
    config_path = CLIENTS_DIR / f"{slug}.json"
    try:
        config = load_config(str(config_path))
    except ConfigError as e:
        print(f"Error loading {slug}: {e}", file=sys.stderr)
        return

    print(f"Fetching threads for {config.client_name}...", file=sys.stderr)
    threads = fetch_all_threads(config.subreddits, sort=config.sort, limit=config.max_threads)

    if json_out is not None:
        if not threads:
            print(f"Warning: no threads fetched for {slug}, skipping JSON output", file=sys.stderr)
            return
        out_path = Path(json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([dataclasses.asdict(t) for t in threads], f, ensure_ascii=False, indent=2)
        print(f"Wrote {len(threads)} threads to {json_out}", file=sys.stderr)
        return

    print(f"\n=== {config.client_name} — Reddit Threads ({len(threads)} total) ===\n")

    for i, t in enumerate(threads, 1):
        print(f"[{i}] r/{t.subreddit}")
        print(f"TITLE: {t.title}")
        print(f"URL: {t.url}")
        print(f"UPVOTES: {t.upvotes} | COMMENTS: {t.num_comments}")
        body = t.body.strip().replace("\n", " ") if t.body and t.body.strip() else "[link post or no body]"
        print(f"BODY: {body[:400]}")
        print("---")

    print(f"\n--- End of threads ---")
    print(f"Paste everything between the === lines into Claude Code, then run /reddit-{slug}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Reddit threads for a client")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--client", help="Client config slug (e.g. 8msolar)")
    group.add_argument("--all", action="store_true", help="Scrape all configured clients in sequence")
    parser.add_argument("--json-out", dest="json_out", help="Write threads as JSON to this file (only with --client)")
    args = parser.parse_args()

    if args.json_out and args.all:
        print("Error: --json-out cannot be used with --all", file=sys.stderr)
        sys.exit(1)

    if args.all:
        slugs = list_client_slugs()
        if not slugs:
            print("No client configs found in clients/", file=sys.stderr)
            sys.exit(1)
        for slug in slugs:
            scrape_one(slug)
            print()
    else:
        scrape_one(args.client, json_out=args.json_out)


if __name__ == "__main__":
    main()
