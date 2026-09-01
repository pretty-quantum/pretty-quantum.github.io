#!/usr/bin/env python3
"""Generate other-works.html from data/other_works.yaml."""
from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_PATH = ROOT / "data" / "other_works.yaml"
TEMPLATE_PATH = ROOT / "templates" / "other_works.template.html"
OUTPUT_PATH = ROOT / "other-works.html"
PLACEHOLDER = "{{OTHER_WORKS}}"


def esc(v) -> str:
    return html.escape(str(v), quote=True) if v not in (None, "") else ""


def link_for(e: dict) -> str:
    doi = e.get("doi")
    if doi:
        doi = str(doi)
        return doi if doi.startswith(("http://", "https://")) else f"https://doi.org/{doi}"
    return str(e.get("url") or "")


def render_entry(e: dict) -> str:
    authors = ", ".join(esc(x) for x in (e.get("authors") or []))
    title = esc(e.get("title") or "[title to be added]")
    publication = esc(e.get("publication"))
    volume = esc(e.get("volume"))
    pages = esc(e.get("pages"))
    kind = esc(e.get("type"))
    note = esc(e.get("note"))
    link = link_for(e)

    venue = publication
    if volume:
        venue += (" " if venue else "") + volume
    if pages:
        venue += (", " if venue else "") + pages
    if link and venue:
        venue = f'<a class="item-link" href="{esc(link)}">{venue}</a>'

    bits = []
    if authors:
        bits.append(authors + ', ')
    bits.append(f'&quot;{title}&quot;')
    if venue:
        bits.append(', ' + venue)
    if kind:
        bits.append(f' <span class="badge">{kind}</span>')
    if note:
        bits.append('. ' + note)
    bits.append('.')
    return '<li>' + ''.join(bits) + '</li>'


def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    works = data.get("works", []) or []
    if works:
        grouped = defaultdict(list)
        for e in works:
            grouped[str(e.get("year") or "Other")].append(e)
        years = sorted(grouped, key=lambda y: int(y) if y.isdigit() else -1, reverse=True)
        body = "\n".join(
            f'<section class="year-section"><h2>{esc(year)}</h2><ol class="entries">'
            + ''.join(render_entry(e) for e in grouped[year])
            + '</ol></section>'
            for year in years
        )
    else:
        body = '<p class="empty">No entries yet. Add records to data/other_works.yaml.</p>'

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"Missing placeholder {PLACEHOLDER}")
    OUTPUT_PATH.write_text(template.replace(PLACEHOLDER, body), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH.name}: {len(works)} entries")


if __name__ == "__main__":
    main()
