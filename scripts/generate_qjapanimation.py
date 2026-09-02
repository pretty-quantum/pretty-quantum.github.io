#!/usr/bin/env python3
"""Generate qjapanimation.html from data/qjapanimation.yaml."""
from __future__ import annotations

import html
import json
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


def render_intro_body(item: dict) -> str:
    if "text" in item:
        return esc(item["text"])
    return (
        f'{esc(item.get("prefix"))}'
        f'<a href="{esc(item.get("url"))}" target="_blank" rel="noopener noreferrer">'
        f'{esc(item.get("link_text"))}</a>{esc(item.get("suffix"))}'
    )


def render_intro_item(item: dict) -> str:
    return f"<li>{render_intro_body(item)}</li>"


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
    intro_items = data.get("intro", []) or []
    intro_lead = render_intro_body(intro_items[0]) if intro_items else ""
    intro = "\n".join(render_intro_item(x) for x in intro_items[1:])
    sections = "\n\n".join(render_section(s) for s in data.get("sections", []) or [])
    total = sum(len(s.get("entries", []) or []) for s in data.get("sections", []) or [])
    return f'''<div class="qja-root">
  <main class="qja-page">
    <header class="qja-header">
      <p class="qja-author">{esc(page.get("author"))} <span class="qja-author-sep">·</span> <a class="qja-pdf-link" href="qjapanimation.pdf">{esc(page.get("pdf_label") or "PDF")}</a></p>
    </header>

    <p class="qja-lead">{intro_lead}</p>

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



def structured_data(data: dict) -> str:
    page = data.get("page", {})
    canonical = page.get("canonical_url") or "https://pretty-quantum.github.io/qjapanimation.html"

    items = []
    position = 1
    for section in data.get("sections", []) or []:
        for entry in section.get("entries", []) or []:
            title = entry.get("title")
            if not title:
                continue
            items.append({
                "@type": "ListItem",
                "position": position,
                "item": {
                    "@type": "CreativeWork",
                    "name": str(title),
                },
            })
            position += 1

    payload = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": page.get("title"),
        "headline": page.get("title"),
        "description": page.get("description"),
        "url": canonical,
        "inLanguage": "ja",
        "dateModified": str(page.get("updated") or ""),
        "author": {
            "@type": "Person",
            "name": page.get("author") or "生田力三",
        },
        "keywords": [
            "量子情報",
            "量子通信",
            "量子コンピュータ",
            "量子もつれ",
            "量子テレポーテーション",
            "量子暗号",
            "量子アルゴリズム",
            "量子力学",
            "多世界解釈",
            "シュレーディンガーの猫",
            "アニメ",
            "漫画",
        ],
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(items),
            "itemListElement": items,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    page = data.get("page", {})
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    output = (template
              .replace("{{META_DESCRIPTION}}", esc(page.get("description")))
              .replace("{{CANONICAL_URL}}", esc(page.get("canonical_url") or "https://pretty-quantum.github.io/qjapanimation.html"))
              .replace("{{HTML_TITLE}}", esc(page.get("html_title") or page.get("title") or "Qjapanimation"))
              .replace("{{SITE_TITLE}}", esc(page.get("title") or page.get("site_title") or "Qjapanimation"))
              .replace("{{STRUCTURED_DATA}}", structured_data(data))
              .replace("{{QJA_CONTENT}}", render_content(data)))
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    total = sum(len(s.get("entries", []) or []) for s in data.get("sections", []) or [])
    print(f"Generated qjapanimation.html: {total} entries")


if __name__ == "__main__":
    main()
