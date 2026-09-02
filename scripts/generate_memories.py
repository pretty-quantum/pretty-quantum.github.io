#!/usr/bin/env python3
"""Generate memories.html from presentations.yaml + memories.yaml."""
from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
import yaml

from generate_presentations import aliases, render_entry, nav, esc, format_date

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
PRESENTATIONS_PATH = ROOT / "data" / "presentations.yaml"
MEMORIES_PATH = ROOT / "data" / "memories.yaml"
TEMPLATE_PATH = ROOT / "templates" / "memories.template.html"


def event_date_text(event: dict) -> str:
    start = format_date(event.get("date_start"))
    end = format_date(event.get("date_end"))
    if start and end:
        return start if start == end else f"{start}–{end}"
    return start or end


def event_as_presentation(event: dict) -> dict | None:
    """Convert a standalone formal presentation to the normal presentation schema."""
    if not event.get("presentation_title"):
        return None
    return {
        "authors": event.get("authors") or [],
        "title": event.get("presentation_title"),
        "presentation_type": event.get("presentation_type"),
        "presentation_date": event.get("presentation_date"),
        "presentation_end_date": None,
        "conference": event.get("conference") or "",
        "conference_start": event.get("date_start"),
        "conference_end": event.get("date_end"),
        "location": event.get("location"),
        "url": None,
        "note": None,
    }


def render_standalone_event(event: dict, alias_set: set[str]) -> str:
    formal = event_as_presentation(event)
    if formal:
        return f'<ol class="entries memory-formal">{render_entry(formal, alias_set)}</ol>'
    title = esc(event.get("title") or "Memory")
    date = esc(event_date_text(event))
    location = esc(event.get("location"))
    meta = " / ".join(x for x in [date, location] if x)
    meta_html = f'<div class="memory-event-meta">{meta}</div>' if meta else ""
    return f'<div class="memory-event"><div class="memory-event-title">{title}</div>{meta_html}</div>'


def render_photos(names: list[str], photo_dir: str) -> str:
    rendered = []
    for name in names or []:
        relative = Path(photo_dir) / str(name)
        path = ROOT / relative
        # Do not create broken image elements before the user uploads the photos.
        if not path.is_file():
            continue
        href = esc(relative.as_posix())
        rendered.append(
            f'<a href="{href}" class="memory-photo-link">'
            f'<img src="{href}" alt="" loading="lazy"></a>'
        )
    return f'<div class="memory-photos">{"".join(rendered)}</div>' if rendered else ""


def memory_year(memory: dict, presentation: dict | None) -> str:
    if presentation:
        date = presentation.get("conference_start") or presentation.get("presentation_date")
    else:
        date = (memory.get("event") or {}).get("date_start")
    return str(date)[:4] if date else "Other"


def render_memory(memory: dict, presentation: dict | None, alias_set: set[str], photo_dir: str) -> str:
    if presentation:
        formal = f'<ol class="entries memory-formal">{render_entry(presentation, alias_set)}</ol>'
    else:
        formal = render_standalone_event(memory.get("event") or {}, alias_set)
    comment = esc(memory.get("comment"))
    comment_html = f'<p class="memory-comment">{comment}</p>' if comment else ""
    photos = render_photos(memory.get("photos") or [], photo_dir)
    return f'<article class="memory-card">{formal}{comment_html}{photos}</article>'


def main() -> None:
    pdata = yaml.safe_load(PRESENTATIONS_PATH.read_text(encoding="utf-8")) or {}
    mdata = yaml.safe_load(MEMORIES_PATH.read_text(encoding="utf-8")) or {}
    entries = pdata.get("presentations", [])
    by_id = {}
    for e in entries:
        pid = e.get("id")
        if pid in by_id:
            raise ValueError(f"Duplicate presentation id: {pid}")
        by_id[pid] = e

    alias_set = aliases(pdata)
    photo_dir = str(mdata.get("photo_dir") or "assets/memories")
    grouped = defaultdict(list)
    missing_links = []
    for memory in mdata.get("memories", []) or []:
        pid = memory.get("presentation_id")
        presentation = by_id.get(pid) if pid else None
        if pid and presentation is None:
            missing_links.append(pid)
        grouped[memory_year(memory, presentation)].append((memory, presentation))
    if missing_links:
        raise ValueError("Unknown presentation_id(s): " + ", ".join(missing_links))

    def year_key(y: str):
        try:
            return (0, -int(y))
        except ValueError:
            return (1, y)

    sections = []
    for year in sorted(grouped, key=year_key):
        cards = "\n".join(render_memory(m, p, alias_set, photo_dir) for m, p in grouped[year])
        sections.append(f'<section class="memory-year"><h2>{esc(year)}</h2>{cards}</section>')

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    output = (template
              .replace("{{NAVIGATION}}", nav("presentations"))
              .replace("{{MEMORIES}}", "\n".join(sections)))
    (ROOT / "memories.html").write_text(output, encoding="utf-8")
    print(f"Generated memories.html: {sum(len(v) for v in grouped.values())} memories")


if __name__ == "__main__":
    main()
