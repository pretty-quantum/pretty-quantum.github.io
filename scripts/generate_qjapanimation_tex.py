#!/usr/bin/env python3
"""Generate qjapanimation.tex from data/qjapanimation.yaml."""
from __future__ import annotations

from pathlib import Path
import re
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_PATH = ROOT / "data" / "qjapanimation.yaml"
TEMPLATE_PATH = ROOT / "templates" / "qjapanimation.template.tex"
OUTPUT_PATH = ROOT / "qjapanimation.tex"

_LATEX_SPECIAL = re.compile(r"([#$%&_{}])")


def tex(value) -> str:
    """Escape plain YAML text for LuaLaTeX."""
    if value in (None, ""):
        return ""
    s = str(value)
    s = s.replace("\\", r"\textbackslash{}")
    s = _LATEX_SPECIAL.sub(r"\\\1", s)
    s = s.replace("~", r"\textasciitilde{}")
    s = s.replace("^", r"\textasciicircum{}")
    return s


def tex_url(value) -> str:
    """Escape a URL used as the first argument of \\href."""
    if value in (None, ""):
        return ""
    return str(value).replace("%", r"\%").replace("#", r"\#")


def render_intro(item: dict) -> str:
    if "text" in item:
        body = tex(item.get("text"))
    else:
        body = (
            tex(item.get("prefix"))
            + r"\href{" + tex_url(item.get("url")) + "}{" + tex(item.get("link_text")) + "}"
            + tex(item.get("suffix"))
        )
    return "  \\item " + body


def values(entry: dict, key: str) -> list[str]:
    return [str(x) for x in (entry.get(key) or []) if x not in (None, "")]


def render_entry(entry: dict) -> str:
    year = tex(entry.get("year") if entry.get("year") else "--")
    title = tex(entry.get("title"))
    content = values(entry, "content")
    note = values(entry, "note")
    n_rows = max(1, len(content), len(note))

    rows = []
    for i in range(n_rows):
        c = tex(content[i]) if i < len(content) else ""
        n = tex(note[i]) if i < len(note) else ""
        y = year if i == 0 else ""
        t = title if i == 0 else ""
        rows.append(f"  {y} & {t} & {c} & {n} \\\\")
    rows.append(r"  \hline")
    return "\n".join(rows)


def render_section(section: dict, index: int) -> str:
    title = tex(section.get("title"))
    body = "\n".join(render_entry(entry) for entry in (section.get("entries") or []))
    table = (
        f"\\section*{{{title}}}\n"
        r"\small" "\n"
        r"\begin{longtable}{C{13mm}|Y{46mm}|Y{106mm}|Y{99.5mm}}" "\n"
        r"\QJATableHeader" "\n"
        r"\endfirsthead" "\n"
        r"\QJATableHeader" "\n"
        r"\endhead" "\n"
        + body + "\n"
        r"\end{longtable}" "\n"
        r"\normalsize"
    )
    return (r"\clearpage" + "\n" + table) if index else table


def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    page = data.get("page", {})
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    intro = "\n".join(render_intro(item) for item in (data.get("intro") or []))
    sections = "\n\n".join(
        render_section(section, i)
        for i, section in enumerate(data.get("sections") or [])
    )

    output = (
        template
        .replace("{{PDF_TITLE}}", tex(page.get("title")))
        .replace("{{PDF_AUTHOR}}", tex(page.get("author")))
        .replace("{{TITLE}}", tex(page.get("title")))
        .replace("{{AUTHOR}}", tex(page.get("author")))
        .replace("{{INTRO}}", intro)
        .replace("{{SECTIONS}}", sections)
        .replace("{{FOOTNOTE}}", tex(page.get("footnote")))
    )

    OUTPUT_PATH.write_text(output, encoding="utf-8")
    total = sum(len(section.get("entries") or []) for section in (data.get("sections") or []))
    print(f"Generated qjapanimation.tex: {total} entries")


if __name__ == "__main__":
    main()
