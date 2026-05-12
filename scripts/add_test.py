#!/usr/bin/env python3
"""Add one lab test JSON record, then rebuild the site.

By default this refuses duplicate tests and prints the existing GitHub Pages URL.
Use --update-existing when intentionally replacing an existing card.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "tests"
PAGES_BASE_URL = "https://luke1001.github.io/lab-test-cards"

REQUIRED = {
    "short_name",
    "full_name",
    "pronunciation",
    "category",
    "accent",
    "icons",
    "what_it_is",
    "why_ordered",
    "specimen",
    "container",
    "helper_cues",
    "memory_hook",
    "updated",
}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def load_existing() -> list[dict]:
    cards = []
    for path in sorted(DATA_DIR.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        card["_path"] = path
        cards.append(card)
    return cards


def duplicate_for(card: dict) -> dict | None:
    slug = card["slug"]
    names = {normalize(card["short_name"]), normalize(card["full_name"]), normalize(slug)}
    for existing in load_existing():
        existing_names = {
            normalize(existing.get("slug", "")),
            normalize(existing.get("short_name", "")),
            normalize(existing.get("full_name", "")),
        }
        aliases = existing.get("aliases", [])
        if isinstance(aliases, list):
            existing_names.update(normalize(str(alias)) for alias in aliases)
        if slug == existing.get("slug") or names & existing_names:
            return existing
    return None


def page_url(card: dict) -> str:
    return f"{PAGES_BASE_URL}/tests/{card['slug']}.html"


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or update a lab test card JSON file.")
    parser.add_argument("json_file", help="Path to a JSON card record.")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Replace an existing matching test instead of refusing as a duplicate.",
    )
    args = parser.parse_args()

    source = Path(args.json_file)
    card = json.loads(source.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(card))
    if missing:
        raise SystemExit(f"missing required fields: {', '.join(missing)}")
    card["slug"] = card.get("slug") or slugify(card["short_name"])

    duplicate = duplicate_for(card)
    if duplicate and not args.update_existing:
        print(f"duplicate test found: {duplicate['short_name']} - {duplicate['full_name']}")
        print(f"existing page: {page_url(duplicate)}")
        raise SystemExit(2)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / f"{card['slug']}.json"
    target.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "scripts/build_site.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/validate_site.py"], cwd=ROOT, check=True)
    print(f"updated {target}")


if __name__ == "__main__":
    main()
