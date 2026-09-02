#!/usr/bin/env python3
"""Generate qjapanimation.html from data/qjapanimation.yaml."""
from __future__ import annotations

import html
from pathlib import Path
import unicodedata
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_PATH = ROOT / "data" / "qjapanimation.yaml"
TEMPLATE_PATH = ROOT / "templates" / "qjapanimation.template.html"
OUTPUT_PATH = ROOT / "qjapanimation.html"


def esc(value) -> str:
    return html.escape(str(value), quote=True) if value not in (None, "") else ""


def render_intro_item(item: dict) -> str:
    if "text" in item:
        return f"<li>{esc(item['text'])}</li>"
    return (
        f'<li>{esc(item.get("prefix"))}'
        f'<a href="{esc(item.get("url"))}" target="_blank" rel="noopener noreferrer">'
        f'{esc(item.get("link_text"))}</a>{esc(item.get("suffix"))}</li>'
    )


def render_lines(lines: list[str], muted_if_empty: bool = False) -> str:
    values = [str(x) for x in (lines or []) if x not in (None, "")]
    if not values and muted_if_empty:
        return '<div class="qja-cell-line"><span class="qja-muted">—</span></div>'
    return "".join(f'<div class="qja-cell-line">{esc(x)}</div>' for x in values)


def search_text(entry: dict) -> str:
    pieces = [
        str(entry.get("year") or "-"),
        str(entry.get("title") or ""),
        *(str(x) for x in entry.get("content", []) or []),
        *(str(x) for x in entry.get("note", []) or []),
    ]
    return unicodedata.normalize("NFKC", " ".join(pieces)).casefold().strip()


def render_entry(entry: dict) -> str:
    year = entry.get("year")
    year_attr = str(year) if year else ""
    year_text = str(year) if year else "—"
    return (
        f'<tr data-year="{esc(year_attr)}" data-search="{esc(search_text(entry))}">\n'
        f'  <td class="qja-year"><span>{esc(year_text)}</span></td>\n'
        f'  <td class="qja-title">{esc(entry.get("title"))}</td>\n'
        f'  <td>{render_lines(entry.get("content", []))}</td>\n'
        f'  <td class="qja-note">{render_lines(entry.get("note", []), muted_if_empty=True)}</td>\n'
        f'</tr>'
    )


def render_section(section: dict) -> str:
    rows = "\n".join(render_entry(e) for e in section.get("entries", []) or [])
    sec_id = esc(section.get("id") or "section")
    return f'''<section id="qja-{sec_id}-section" class="qja-section">
  <h2>{esc(section.get("title"))}</h2>
  <div class="qja-table-frame">
    <table class="qja-table">
      <caption>{esc(section.get("caption"))}</caption>
      <thead><tr><th>年</th><th>タイトル</th><th>内容</th><th>備考</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>
</section>'''


def render_content(data: dict) -> str:
    page = data.get("page", {})
    intro = "\n".join(render_intro_item(x) for x in data.get("intro", []) or [])
    sections = "\n\n".join(render_section(s) for s in data.get("sections", []) or [])
    total = sum(len(s.get("entries", []) or []) for s in data.get("sections", []) or [])
    return f'''<div class="qja-root">
  <main class="qja-page">
    <header class="qja-header">
      <h1>{esc(page.get("title"))}</h1>
      <p class="qja-author">{esc(page.get("author"))} <span class="qja-author-sep">·</span> <a class="qja-pdf-link" href="qjapanimation.pdf">{esc(page.get("pdf_label") or "PDF")}</a></p>
    </header>

    <aside class="qja-intro"><ul>
{intro}
    </ul></aside>

    <div class="qja-controls" aria-label="表の検索と絞り込み">
      <input id="qja-search" class="qja-input" type="search" placeholder="タイトル・内容・備考を検索" aria-label="タイトル・内容・備考を検索">
      <select id="qja-year-filter" class="qja-select" aria-label="年で絞り込む">
        <option value="">すべての年</option>
        <option value="unknown">年不明</option>
      </select>
      <button id="qja-reset" class="qja-button" type="button">リセット</button>
    </div>

    <p id="qja-count" class="qja-count">{total}件を表示</p>

{sections}

    <div id="qja-empty" class="qja-empty">該当する項目はありません。</div>
    <p class="qja-footnote">{esc(page.get("footnote"))}</p>
  </main>
</div>'''


def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    page = data.get("page", {})
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    output = (template
              .replace("{{META_DESCRIPTION}}", esc(page.get("description")))
              .replace("{{SITE_TITLE}}", esc(page.get("site_title") or "Qjapanimation"))
              .replace("{{QJA_CONTENT}}", render_content(data)))
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    total = sum(len(s.get("entries", []) or []) for s in data.get("sections", []) or [])
    print(f"Generated qjapanimation.html: {total} entries")


if __name__ == "__main__":
    main()
