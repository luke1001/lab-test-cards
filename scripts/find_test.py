#!/usr/bin/env python3
"""Find an existing lab test card and print its GitHub Pages URL."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "tests"
PAGES_BASE_URL = "https://luke1001.github.io/lab-test-cards"


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def page_url(slug: str) -> str:
    return f"{PAGES_BASE_URL}/tests/{slug}.html"


def main() -> None:
    parser = argparse.ArgumentParser(description="Find an existing lab test card.")
    parser.add_argument("query", help="Test abbreviation, name, or slug.")
    args = parser.parse_args()
    query = normalize(args.query)

    matches = []
    for path in sorted(DATA_DIR.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        values = [
            card.get("slug", ""),
            card.get("short_name", ""),
            card.get("full_name", ""),
            *card.get("aliases", []),
        ]
        normalized = {normalize(str(value)) for value in values}
        if query in normalized:
            matches.append(card)

    if not matches:
        raise SystemExit(1)

    for card in matches:
        print(f"{card['short_name']} - {card['full_name']}")
        print(page_url(card["slug"]))


if __name__ == "__main__":
    main()
