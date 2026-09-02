#!/usr/bin/env python3
"""Generate memories.html as an augmented view of presentations.yaml.

Memories shows every presentation exactly as Presentations does.  If a
presentation has a matching entry in memories.yaml, its comment/photos are
appended below it.  Standalone events in memories.yaml are inserted as
additional entries in chronological position.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import yaml

from generate_presentations import (
    aliases,
    esc,
    format_authors,
    format_date,
    period_text,
    presentation_date_text,
    nav,
)

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
PRESENTATIONS_PATH = ROOT / "data" / "presentations.yaml"
MEMORIES_PATH = ROOT / "data" / "memories.yaml"
TEMPLATE_PATH = ROOT / "templates" / "memories.template.html"


def presentation_body(e: dict, alias_set: set[str]) -> str:
    """Same visible presentation text as generate_presentations.render_entry()."""
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
    return "".join(pieces)


def event_date_text(event: dict) -> str:
    start = format_date(event.get("date_start"))
    end = format_date(event.get("date_end"))
    if start and end:
        return start if start == end else f"{start}–{end}"
    return start or end


def event_body(event: dict) -> str:
    """Render a standalone event as a presentation-list-style entry."""
    title = esc(event.get("title") or "Memory")
    date = esc(event_date_text(event))
    location = esc(event.get("location"))
    pieces = [title]
    if date:
        pieces.append(f", {date}")
    if location:
        pieces.append(f", {location}")
    pieces.append(".")
    return "".join(pieces)


def render_photos(names: list[str], photo_dir: str) -> str:
    rendered = []
    for name in names or []:
        relative = Path(photo_dir) / str(name)
        path = ROOT / relative
        # Avoid broken images before a photo has actually been uploaded.
        if not path.is_file():
            continue
        href = esc(relative.as_posix())
        rendered.append(
            f'<a href="{href}" class="memory-photo-link">'
            f'<img src="{href}" alt="" loading="lazy"></a>'
        )
    return f'<div class="memory-photos">{"".join(rendered)}</div>' if rendered else ""


def render_extra(memory: dict | None, photo_dir: str) -> str:
    if not memory:
        return ""
    comment = esc(memory.get("comment"))
    comment_html = f'<p class="memory-comment">{comment}</p>' if comment else ""
    photos = render_photos(memory.get("photos") or [], photo_dir)
    if not comment_html and not photos:
        return ""
    return f'<div class="memory-extra">{comment_html}{photos}</div>'


def presentation_sort_date(e: dict) -> str:
    return str(
        e.get("conference_start")
        or e.get("presentation_date")
        or e.get("conference_end")
        or ""
    )


def standalone_sort_date(memory: dict) -> str:
    event = memory.get("event") or {}
    return str(event.get("date_start") or event.get("date_end") or "")


def standalone_year(memory: dict) -> str:
    event = memory.get("event") or {}
    date = event.get("date_start") or event.get("date_end")
    return str(date)[:4] if date else "Other"


def insert_standalones_preserving_presentation_order(
    presentations: list[dict],
    standalone_memories: list[dict],
) -> list[tuple[str, dict]]:
    """Keep presentation relative order and insert standalone events by date."""
    merged: list[tuple[str, dict]] = [("presentation", e) for e in presentations]

    for memory in sorted(standalone_memories, key=standalone_sort_date, reverse=True):
        mdate = standalone_sort_date(memory)
        insert_at = len(merged)
        for i, (kind, obj) in enumerate(merged):
            if kind != "presentation":
                continue
            pdate = presentation_sort_date(obj)
            if pdate and mdate and pdate < mdate:
                insert_at = i
                break
        merged.insert(insert_at, ("standalone", memory))
    return merged


def render_scope(
    entries: list[dict],
    scope: str,
    memory_by_pid: dict[str, dict],
    standalone_memories: list[dict],
    alias_set: set[str],
    photo_dir: str,
) -> str:
    presentations = [e for e in entries if e.get("scope") == scope]

    grouped_presentations = defaultdict(list)
    year_order = []
    for e in presentations:
        year = str(e.get("fiscal_year") or "Other")
        if year not in grouped_presentations:
            year_order.append(year)
        grouped_presentations[year].append(e)

    grouped_standalone = defaultdict(list)
    for memory in standalone_memories:
        event = memory.get("event") or {}
        if event.get("scope") != scope:
            continue
        grouped_standalone[standalone_year(memory)].append(memory)

    all_years = set(year_order) | set(grouped_standalone)
    try:
        ordered_years = sorted(all_years, key=lambda y: int(y), reverse=True)
    except ValueError:
        ordered_years = year_order + [y for y in grouped_standalone if y not in year_order]

    sections = []
    for year in ordered_years:
        merged = insert_standalones_preserving_presentation_order(
            grouped_presentations.get(year, []),
            grouped_standalone.get(year, []),
        )

        items = []
        for kind, obj in merged:
            if kind == "presentation":
                pid = obj.get("id")
                memory = memory_by_pid.get(pid)
                body = presentation_body(obj, alias_set)
                extra = render_extra(memory, photo_dir)
                cls = ' class="memory-augmented"' if extra else ""
                items.append(f"<li{cls}>{body}{extra}</li>")
            else:
                event = obj.get("event") or {}
                body = event_body(event)
                extra = render_extra(obj, photo_dir)
                items.append(f'<li class="memory-standalone">{body}{extra}</li>')

        sections.append(
            f'<section class="year-section"><h2>{esc(year)}</h2>'
            f'<ol class="entries">{"".join(items)}</ol></section>'
        )

    return "\n".join(sections) if sections else '<p class="empty">No entries yet.</p>'


def main() -> None:
    pdata = yaml.safe_load(PRESENTATIONS_PATH.read_text(encoding="utf-8")) or {}
    mdata = yaml.safe_load(MEMORIES_PATH.read_text(encoding="utf-8")) or {}

    entries = pdata.get("presentations", [])
    by_id = {}
    for e in entries:
        pid = e.get("id")
        if not pid:
            raise ValueError("Every presentation needs an id for Memories.")
        if pid in by_id:
            raise ValueError(f"Duplicate presentation id: {pid}")
        by_id[pid] = e

    memory_by_pid: dict[str, dict] = {}
    standalone_memories: list[dict] = []
    missing_links = []

    for memory in mdata.get("memories", []) or []:
        pid = memory.get("presentation_id")
        if pid:
            if pid not in by_id:
                missing_links.append(pid)
                continue
            if pid in memory_by_pid:
                raise ValueError(f"Duplicate memory for presentation_id: {pid}")
            memory_by_pid[pid] = memory
        else:
            standalone_memories.append(memory)

    if missing_links:
        raise ValueError("Unknown presentation_id(s): " + ", ".join(missing_links))

    alias_set = aliases(pdata)
    photo_dir = str(mdata.get("photo_dir") or "assets/memories")

    international = render_scope(
        entries, "international", memory_by_pid, standalone_memories, alias_set, photo_dir
    )
    domestic = render_scope(
        entries, "domestic", memory_by_pid, standalone_memories, alias_set, photo_dir
    )

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    output = (
        template
        .replace("{{NAVIGATION}}", nav("presentations"))
        .replace("{{INTERNATIONAL_MEMORIES}}", international)
        .replace("{{DOMESTIC_MEMORIES}}", domestic)
    )
    (ROOT / "memories.html").write_text(output, encoding="utf-8")

    formal_count = len(entries)
    standalone_count = len(standalone_memories)
    augmented_count = len(memory_by_pid) + standalone_count
    print(
        "Generated memories.html: "
        f"{formal_count} presentations + {standalone_count} standalone events "
        f"= {formal_count + standalone_count} entries; "
        f"{augmented_count} entries have memories"
    )


if __name__ == "__main__":
    main()
