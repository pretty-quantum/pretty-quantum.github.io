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
    # Preserve author order without special emphasis.
    return ", ".join(esc(name) for name in (authors or []))


def format_date(value) -> str:
    """Format ISO-like YAML dates for HTML display."""
    if value in (None, ""):
        return ""
    text = str(value)
    # YYYY-MM-DD -> YYYY/MM/DD, and YYYY-MM -> YYYY/MM.
    if len(text) in (7, 10) and text[4] == "-" and (len(text) == 7 or text[7] == "-"):
        return text.replace("-", "/")
    return text


def period_text(e: dict) -> str:
    start, end = e.get("conference_start"), e.get("conference_end")
    start_text, end_text = format_date(start), format_date(end)
    if start_text and end_text:
        return start_text if start_text == end_text else f"{start_text}–{end_text}"
    return start_text or end_text


def presentation_date_text(e: dict) -> str:
    start, end = e.get("presentation_date"), e.get("presentation_end_date")
    start_text, end_text = format_date(start), format_date(end)
    if start_text and end_text:
        return start_text if start_text == end_text else f"{start_text}–{end_text}"
    return start_text or end_text


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
    return f"<li>{''.join(pieces)}</li>"


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
        ("presentations.html", "Presentations", "presentations"),
        ("guide.html", "Guide", "guide"),
        ("qjapanimation.html", "Qjapanimation", "qja"),
    ]
    return '<nav class="nav">' + ''.join(
        f'<a href="{href}"' + (' class="active"' if key == active else '') + f'>{label}</a>'
        for href, label, key in links
    ) + '</nav>'


def redirect_page(target: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url={target}">
  <link rel="canonical" href="{target}">
  <title>Redirecting…</title>
</head>
<body>
  <p><a href="{target}">Continue to presentations</a></p>
</body>
</html>
"""


def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    entries = data.get("presentations", [])
    alias_set = aliases(data)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    international = render_scope(entries, "international", alias_set)
    domestic = render_scope(entries, "domestic", alias_set)

    output = (template
              .replace("{{PAGE_TITLE}}", "Presentations")
              .replace("{{NAVIGATION}}", nav("presentations"))
              .replace("{{INTERNATIONAL_PRESENTATIONS}}", international)
              .replace("{{DOMESTIC_PRESENTATIONS}}", domestic))

    (ROOT / "presentations.html").write_text(output, encoding="utf-8")

    # Backward compatibility for old URLs/bookmarks.
    (ROOT / "international.html").write_text(
        redirect_page("presentations.html#international"), encoding="utf-8")
    (ROOT / "domestic.html").write_text(
        redirect_page("presentations.html#domestic"), encoding="utf-8")

    international_count = sum(e.get("scope") == "international" for e in entries)
    domestic_count = sum(e.get("scope") == "domestic" for e in entries)
    print(
        f"Generated presentations.html: "
        f"{international_count} international + {domestic_count} domestic entries"
    )


if __name__ == "__main__":
    main()
