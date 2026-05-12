#!/usr/bin/env python3
"""Add or update one lab test JSON record, then rebuild the site."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "tests"

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or update a lab test card JSON file.")
    parser.add_argument("json_file", help="Path to a JSON card record.")
    args = parser.parse_args()

    source = Path(args.json_file)
    card = json.loads(source.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(card))
    if missing:
        raise SystemExit(f"missing required fields: {', '.join(missing)}")
    card["slug"] = card.get("slug") or slugify(card["short_name"])

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target = DATA_DIR / f"{card['slug']}.json"
    target.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "scripts/build_site.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/validate_site.py"], cwd=ROOT, check=True)
    print(f"updated {target}")


if __name__ == "__main__":
    main()
