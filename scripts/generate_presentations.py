#!/usr/bin/env python3
"""Generate international.html and domestic.html from data/presentations.yaml."""
from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_PATH = ROOT / "data" / "presentations.yaml"
TEMPLATE_PATH = ROOT / "templates" / "presentations.template.html"


def esc(value) -> str:
    return html.escape(str(value), quote=True) if value not in (None, "") else ""


def aliases(data: dict) -> set[str]:
    return {str(x).replace(" ", "").casefold() for x in data.get("person", {}).get("aliases", [])}


def is_me(name: str, alias_set: set[str]) -> bool:
    return str(name).replace(" ", "").casefold() in alias_set


def format_authors(authors: list[str], alias_set: set[str]) -> str:
    out = []
    for name in authors or []:
        text = esc(name)
        if is_me(name, alias_set):
            text = f"<strong>{text}</strong>"
        out.append(text)
    return ", ".join(out)


def period_text(e: dict) -> str:
    start, end = e.get("conference_start"), e.get("conference_end")
    if start and end:
        return str(start) if start == end else f"{start}–{end}"
    return str(start or end or "")


def presentation_date_text(e: dict) -> str:
    start, end = e.get("presentation_date"), e.get("presentation_end_date")
    if start and end:
        return str(start) if start == end else f"{start}–{end}"
    return str(start or end or "")


def render_entry(e: dict, alias_set: set[str]) -> str:
    authors = format_authors(e.get("authors", []), alias_set)
    title = esc(e.get("title") or "[title to be added]")
    ptype = esc(e.get("presentation_type"))
    pdate = esc(presentation_date_text(e))
    conference = esc(e.get("conference") or "[conference to be added]")
    location = esc(e.get("location"))
    cperiod = esc(period_text(e))
    url = e.get("url")
    note = esc(e.get("note"))

    if url:
        conference = f'<a class="item-link" href="{esc(url)}">{conference}</a>'

    first_author_is_me = bool(e.get("authors")) and is_me(e["authors"][0], alias_set)
    presenter_badge = '<span class="badge">Presenter</span>' if first_author_is_me else ""

    pieces = [f'{authors}, &quot;{title}&quot;']
    meta = []
    if ptype:
        meta.append(ptype)
    if pdate:
        meta.append(pdate)
    if meta:
        pieces.append(f" ({', '.join(meta)})")
    pieces.append(f", {conference}")
    if cperiod:
        pieces.append(f", {cperiod}")
    if location:
        pieces.append(f", {location}")
    if note:
        pieces.append(f". {note}")
    pieces.append(".")
    return f"<li>{''.join(pieces)} {presenter_badge}</li>"


def render_scope(entries: list[dict], scope: str, alias_set: set[str]) -> str:
    selected = [e for e in entries if e.get("scope") == scope]
    grouped = defaultdict(list)
    order = []
    for e in selected:
        year = str(e.get("fiscal_year") or "Other")
        if year not in grouped:
            order.append(year)
        grouped[year].append(e)
    try:
        order.sort(key=lambda y: int(y), reverse=True)
    except ValueError:
        pass

    sections = []
    for year in order:
        items = "".join(render_entry(e, alias_set) for e in grouped[year])
        sections.append(f'<section class="year-section"><h2>{esc(year)}</h2><ol class="entries">{items}</ol></section>')
    return "\n".join(sections) if sections else '<p class="empty">No entries yet.</p>'


def nav(active: str) -> str:
    links = [
        ("index.html", "Home", "home"),
        ("publications.html", "Publications", "publications"),
        ("international.html", "International", "international"),
        ("domestic.html", "Domestic", "domestic"),
        ("other-works.html", "Other works", "other"),
        ("guide.html", "Guide", "guide"),
        ("qjapanimation.html", "Qjapanimation", "qja"),
    ]
    return '<nav class="nav">' + ''.join(
        f'<a href="{href}"' + (' class="active"' if key == active else '') + f'>{label}</a>'
        for href, label, key in links
    ) + '</nav>'

def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    entries = data.get("presentations", [])
    alias_set = aliases(data)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for scope, filename, title in [
        ("international", "international.html", "International presentations"),
        ("domestic", "domestic.html", "Domestic presentations"),
    ]:
        body = render_scope(entries, scope, alias_set)
        output = (template
                  .replace("{{PAGE_TITLE}}", title)
                  .replace("{{NAVIGATION}}", nav(scope))
                  .replace("{{PRESENTATIONS}}", body))
        (ROOT / filename).write_text(output, encoding="utf-8")
        count = sum(e.get("scope") == scope for e in entries)
        print(f"Generated {filename}: {count} entries")


if __name__ == "__main__":
    main()
