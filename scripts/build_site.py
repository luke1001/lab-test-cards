#!/usr/bin/env python3
"""Build the Lab Test Cards static GitHub Pages site."""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "tests"
DOCS_DIR = ROOT / "docs"
CARDS_DIR = DOCS_DIR / "cards"
TESTS_DIR = DOCS_DIR / "tests"
ASSETS_DIR = DOCS_DIR / "assets"
CATALOG_PATH = DOCS_DIR / "data" / "catalog.json"

REQUIRED_FIELDS = {
    "slug",
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

CATEGORY_ORDER = [
    "Hematology",
    "Chemistry",
    "Coagulation",
    "Cardiac",
    "Urinalysis",
    "Microbiology",
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def load_tests() -> list[dict]:
    cards = []
    for path in sorted(DATA_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            card = json.load(f)
        missing = sorted(REQUIRED_FIELDS - set(card))
        if missing:
            raise ValueError(f"{path} missing required fields: {', '.join(missing)}")
        if card["slug"] != path.stem:
            raise ValueError(f"{path} slug must match filename")
        cards.append(card)
    return sorted(cards, key=lambda item: (CATEGORY_ORDER.index(item["category"]) if item["category"] in CATEGORY_ORDER else 99, item["short_name"].lower()))


def text_lines(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def svg_text(x: int, y: int, text: str, size: int = 28, weight: int = 500, fill: str = "#1f2937") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(text)}</text>'


def svg_wrapped(x: int, y: int, text: str, width: int, size: int = 25, gap: int = 32, fill: str = "#374151") -> tuple[str, int]:
    parts = []
    for i, line in enumerate(text_lines(text, width)):
        parts.append(svg_text(x, y + (i * gap), line, size=size, fill=fill))
    return "\n".join(parts), y + max(len(parts), 1) * gap


def svg_bullets(x: int, y: int, bullets: list[str], width: int, accent: str) -> tuple[str, int]:
    parts = []
    cursor = y
    for bullet in bullets:
        parts.append(f'<circle cx="{x}" cy="{cursor - 8}" r="6" fill="{accent}"/>')
        wrapped, next_y = svg_wrapped(x + 22, cursor, bullet, width, size=24, gap=30)
        parts.append(wrapped)
        cursor = next_y + 8
    return "\n".join(parts), cursor


def generate_svg(card: dict) -> str:
    accent = card["accent"]
    icon_labels = card["icons"][:4]
    icon_gap = 146
    icon_parts = []
    for index, label in enumerate(icon_labels):
        x = 92 + (index * icon_gap)
        icon_parts.append(f'<circle cx="{x}" cy="290" r="44" fill="{accent}" opacity="0.14"/>')
        icon_parts.append(svg_text(x - 30, 300, label[:3].upper(), size=22, weight=700, fill=accent))

    why, after_why = svg_bullets(70, 520, card["why_ordered"][:4], 42, accent)
    cues, after_cues = svg_bullets(70, 900, card["helper_cues"][:3], 42, accent)
    what, _ = svg_wrapped(58, 430, card["what_it_is"], 46, size=24)
    specimen = f'{card["specimen"]}; common tube/container: {card["container"]}'
    specimen_text, _ = svg_wrapped(58, 805, specimen, 46, size=24)
    memory_text, _ = svg_wrapped(58, 1098, card["memory_hook"], 46, size=25, fill="#111827")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1280" viewBox="0 0 720 1280" role="img" aria-labelledby="title desc">
  <title id="title">{esc(card["short_name"])} lab test study card</title>
  <desc id="desc">{esc(card["what_it_is"])}</desc>
  <rect width="720" height="1280" rx="36" fill="#ffffff"/>
  <rect x="0" y="0" width="720" height="1280" rx="36" fill="{accent}" opacity="0.045"/>
  <rect x="38" y="38" width="644" height="1204" rx="30" fill="#ffffff" stroke="#d8dee8" stroke-width="3"/>
  <rect x="38" y="38" width="644" height="122" rx="30" fill="{accent}"/>
  {svg_text(58, 104, card["short_name"], size=48, weight=800, fill="#ffffff")}
  {svg_text(58, 144, card["full_name"], size=24, weight=500, fill="#eef6ff")}
  <rect x="508" y="72" width="142" height="42" rx="21" fill="#ffffff" opacity="0.22"/>
  {svg_text(532, 101, card["category"], size=21, weight=700, fill="#ffffff")}
  {svg_text(58, 210, "Pronounced: " + card["pronunciation"], size=26, weight=700, fill="#111827")}
  {"".join(icon_parts)}
  {svg_text(58, 392, "What it is", size=27, weight=800, fill=accent)}
  {what}
  {svg_text(58, 488, "Why it's ordered", size=27, weight=800, fill=accent)}
  {why}
  {svg_text(58, 766, "Common specimen", size=27, weight=800, fill=accent)}
  {specimen_text}
  {svg_text(58, 868, "Lab helper cue", size=27, weight=800, fill=accent)}
  {cues}
  <rect x="58" y="1050" width="604" height="96" rx="22" fill="{accent}" opacity="0.10"/>
  {svg_text(82, 1084, "Memory hook", size=24, weight=800, fill=accent)}
  {memory_text}
  {svg_text(58, 1204, "Quick study card - follow your site's specimen policy and tube guide.", size=20, fill="#64748b")}
</svg>
'''


def page_shell(title: str, body: str, css_href: str = "assets/site.css", extra_head: str = "") -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{esc(css_href)}">
  {extra_head}
</head>
<body>
{body}
</body>
</html>
'''


def generate_test_page(card: dict) -> str:
    why = "\n".join(f"<li>{esc(item)}</li>" for item in card["why_ordered"])
    cues = "\n".join(f"<li>{esc(item)}</li>" for item in card["helper_cues"])
    return page_shell(
        f'{card["short_name"]} Lab Test Card',
        f'''<main class="test-page">
  <nav class="topbar"><a href="../index.html">Lab Test Cards</a><span>{esc(card["category"])}</span></nav>
  <section class="test-hero">
    <div>
      <p class="eyebrow">{esc(card["category"])}</p>
      <h1>{esc(card["short_name"])}</h1>
      <p class="subtitle">{esc(card["full_name"])}</p>
      <p class="pronounce">Pronounced: {esc(card["pronunciation"])}</p>
    </div>
    <a class="card-link" href="../cards/{esc(card["slug"])}.svg">Open SVG</a>
  </section>
  <section class="study-layout">
    <img class="study-card" src="../cards/{esc(card["slug"])}.svg" alt="{esc(card["short_name"])} lab test flashcard">
    <article class="study-notes">
      <h2>What it is</h2>
      <p>{esc(card["what_it_is"])}</p>
      <h2>Why it's ordered</h2>
      <ul>{why}</ul>
      <h2>Common specimen</h2>
      <p>{esc(card["specimen"])}. Common tube/container: {esc(card["container"])}.</p>
      <h2>Lab helper cue</h2>
      <ul>{cues}</ul>
      <h2>Memory hook</h2>
      <p>{esc(card["memory_hook"])}</p>
      <p class="policy-note">Verify specimen, tube, transport, and handling requirements against your local policy.</p>
      <p class="updated">Last updated: {esc(card["updated"])}</p>
    </article>
  </section>
</main>''',
        css_href="../assets/site.css",
    )


def generate_index(cards: list[dict]) -> str:
    categories = sorted({card["category"] for card in cards}, key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99)
    buttons = '<button class="filter active" data-category="all">All</button>' + "".join(
        f'<button class="filter" data-category="{esc(category)}">{esc(category)}</button>' for category in categories
    )
    items = []
    for card in cards:
        items.append(f'''<a class="test-tile" href="tests/{esc(card["slug"])}.html" data-category="{esc(card["category"])}" data-search="{esc((card["short_name"] + " " + card["full_name"] + " " + card["category"]).lower())}">
  <span class="tile-badge" style="--accent:{esc(card["accent"])}">{esc(card["category"])}</span>
  <strong>{esc(card["short_name"])}</strong>
  <span>{esc(card["full_name"])}</span>
</a>''')
    script = '''<script>
const search = document.querySelector('#search');
const filters = [...document.querySelectorAll('.filter')];
const tiles = [...document.querySelectorAll('.test-tile')];
let active = 'all';
function applyFilters() {
  const query = search.value.trim().toLowerCase();
  tiles.forEach(tile => {
    const categoryMatch = active === 'all' || tile.dataset.category === active;
    const searchMatch = !query || tile.dataset.search.includes(query);
    tile.hidden = !(categoryMatch && searchMatch);
  });
}
search.addEventListener('input', applyFilters);
filters.forEach(button => button.addEventListener('click', () => {
  active = button.dataset.category;
  filters.forEach(item => item.classList.toggle('active', item === button));
  applyFilters();
}));
</script>'''
    return page_shell(
        "Lab Test Cards",
        f'''<main class="index-page">
  <section class="index-hero">
    <p class="eyebrow">Hospital lab assistant study cards</p>
    <h1>Lab Test Cards</h1>
    <p>Quick recognition, specimen cues, routing awareness, and memory hooks for common main-lab tests.</p>
    <input id="search" type="search" placeholder="Search CBC, troponin, urine culture..." aria-label="Search lab tests">
    <div class="filters" aria-label="Category filters">{buttons}</div>
  </section>
  <section class="test-grid" aria-label="Common lab tests">
    {"".join(items)}
  </section>
</main>
{script}''',
    )


def write_css() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "site.css").write_text(
        """:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f6f8fb;
  color: #111827;
}
* { box-sizing: border-box; }
body { margin: 0; background: #f6f8fb; }
a { color: inherit; }
.index-page, .test-page { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 56px; }
.index-hero, .test-hero { padding: 28px 0 24px; }
.eyebrow { margin: 0 0 8px; color: #2563eb; font-size: 0.82rem; font-weight: 800; letter-spacing: 0; text-transform: uppercase; }
h1 { margin: 0; font-size: clamp(2.2rem, 8vw, 4.6rem); line-height: 0.96; letter-spacing: 0; }
.index-hero p, .subtitle { max-width: 720px; color: #475569; font-size: 1.05rem; line-height: 1.55; }
#search { width: min(640px, 100%); min-height: 48px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0 14px; font: inherit; background: #fff; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.filter, .card-link { min-height: 38px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0 12px; background: #fff; color: #334155; font: inherit; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; }
.filter.active { background: #111827; border-color: #111827; color: #fff; }
.test-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; }
.test-tile { min-height: 146px; padding: 16px; border: 1px solid #d8dee8; border-radius: 8px; background: #fff; text-decoration: none; display: flex; flex-direction: column; gap: 10px; }
.test-tile:hover { border-color: #94a3b8; box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08); }
.tile-badge { align-self: flex-start; border-left: 4px solid var(--accent); background: #f8fafc; color: #334155; padding: 5px 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 800; }
.test-tile strong { font-size: 1.45rem; }
.test-tile span:last-child { color: #64748b; line-height: 1.35; }
.topbar { min-height: 42px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #d8dee8; color: #475569; font-weight: 800; }
.test-hero { display: flex; gap: 16px; align-items: end; justify-content: space-between; }
.pronounce { margin: 14px 0 0; font-weight: 800; color: #334155; }
.study-layout { display: grid; grid-template-columns: minmax(280px, 420px) minmax(0, 1fr); gap: 28px; align-items: start; }
.study-card { width: 100%; height: auto; border-radius: 18px; box-shadow: 0 18px 48px rgba(15, 23, 42, 0.14); background: #fff; }
.study-notes { background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 24px; }
.study-notes h2 { margin: 22px 0 8px; font-size: 1rem; }
.study-notes h2:first-child { margin-top: 0; }
.study-notes p, .study-notes li { color: #475569; line-height: 1.55; }
.policy-note { margin-top: 22px; padding: 12px; border-left: 4px solid #2563eb; background: #eff6ff; border-radius: 6px; }
.updated { font-size: 0.9rem; color: #64748b; }
@media (max-width: 760px) {
  .study-layout, .test-hero { grid-template-columns: 1fr; display: grid; }
  .card-link { justify-self: start; }
}
@media print {
  body { background: #fff; }
  .topbar, .study-notes, .test-hero, .index-page { display: none; }
  .test-page { width: 100%; padding: 0; }
  .study-layout { display: block; }
  .study-card { box-shadow: none; max-width: 5.2in; }
}
""",
        encoding="utf-8",
    )


def build() -> None:
    cards = load_tests()
    if not cards:
        raise ValueError("No cards found in data/tests")

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    write_css()
    for old in list(CARDS_DIR.glob("*.svg")) + list(TESTS_DIR.glob("*.html")):
        old.unlink()
    for card in cards:
        svg = generate_svg(card)
        ElementTree.fromstring(svg)
        (CARDS_DIR / f'{card["slug"]}.svg').write_text(svg, encoding="utf-8")
        (TESTS_DIR / f'{card["slug"]}.html').write_text(generate_test_page(card), encoding="utf-8")

    (DOCS_DIR / "index.html").write_text(generate_index(cards), encoding="utf-8")
    catalog = [
        {
            "slug": card["slug"],
            "short_name": card["short_name"],
            "full_name": card["full_name"],
            "category": card["category"],
            "updated": card["updated"],
            "url": f'tests/{card["slug"]}.html',
            "card": f'cards/{card["slug"]}.svg',
        }
        for card in cards
    ]
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
