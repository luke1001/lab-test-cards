#!/usr/bin/env python3
"""Validate Lab Test Cards source data and generated site files."""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "tests"
DOCS_DIR = ROOT / "docs"

REQUIRED_LISTS = ("icons", "why_ordered", "helper_cues")
REQUIRED_STRINGS = (
    "slug",
    "short_name",
    "full_name",
    "pronunciation",
    "category",
    "accent",
    "what_it_is",
    "specimen",
    "container",
    "memory_hook",
    "updated",
)


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def main() -> None:
    slugs: set[str] = set()
    for path in sorted(DATA_DIR.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        for field in REQUIRED_STRINGS:
            if not isinstance(card.get(field), str) or not card[field].strip():
                fail(f"{path} has invalid {field}")
        for field in REQUIRED_LISTS:
            if not isinstance(card.get(field), list) or not card[field]:
                fail(f"{path} has invalid {field}")
        if card["slug"] in slugs:
            fail(f"duplicate slug {card['slug']}")
        slugs.add(card["slug"])
        if card["slug"] != path.stem:
            fail(f"{path} filename does not match slug")

    if not slugs:
        fail("no test data found")

    for slug in slugs:
        page = DOCS_DIR / "tests" / f"{slug}.html"
        svg = DOCS_DIR / "cards" / f"{slug}.svg"
        if not page.exists():
            fail(f"missing page for {slug}")
        if not svg.exists():
            fail(f"missing svg for {slug}")
        ElementTree.fromstring(svg.read_text(encoding="utf-8"))
        page_text = page.read_text(encoding="utf-8")
        if f"../cards/{slug}.svg" not in page_text:
            fail(f"{page} does not reference its svg")

    index = DOCS_DIR / "index.html"
    catalog = DOCS_DIR / "data" / "catalog.json"
    if not index.exists():
        fail("missing docs/index.html")
    if not catalog.exists():
        fail("missing docs/data/catalog.json")
    index_text = index.read_text(encoding="utf-8")
    for slug in slugs:
        if f"tests/{slug}.html" not in index_text:
            fail(f"index missing {slug}")
    if 'name="viewport" content="width=device-width, initial-scale=1"' not in index_text:
        fail("index missing responsive viewport meta tag")
    if 'class="alpha-nav"' not in index_text:
        fail("index missing alphabetical navigation")
    if 'class="alpha-section"' not in index_text:
        fail("index missing alphabetical sections")
    forbidden_index = ('id="search"', 'class="filter"', "<script>")
    for forbidden in forbidden_index:
        if forbidden in index_text:
            fail(f"index still contains removed search/filter behavior: {forbidden}")

    css = (DOCS_DIR / "assets" / "site.css").read_text(encoding="utf-8")
    responsive_checks = (
        "@media (max-width: 760px)",
        "@media (max-width: 420px)",
        "repeat(auto-fit, minmax(min(100%, 220px), 1fr))",
        "overflow-x: hidden",
        "overflow-wrap: anywhere",
        ".alpha-nav",
        ".alpha-section",
        "touch-action: manipulation",
    )
    for check in responsive_checks:
        if check not in css:
            fail(f"site css missing responsive rule: {check}")

    sample_page = (DOCS_DIR / "tests" / f"{next(iter(slugs))}.html").read_text(encoding="utf-8")
    if 'name="viewport" content="width=device-width, initial-scale=1"' not in sample_page:
        fail("test pages missing responsive viewport meta tag")
    print(f"validated {len(slugs)} lab test cards")


if __name__ == "__main__":
    main()
