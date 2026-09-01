#!/usr/bin/env python3
"""Generate publications.html from ikuta.bib.

No third-party packages are required.

Rules matched to the current Pretty Quantum publications page:
- group by year, newest first;
- preserve BibTeX order within each year;
- omit proceedings/conference entries from the generated HTML;
- omit an arXiv entry when a non-arXiv entry with the same normalized title exists;
- convert BibTeX author names from "Family, Given" to "Given Family";
- render a literal BibTeX author "others" as "et al.";
- use DOI links when available, otherwise the BibTeX URL;
- for arXiv entries, display and link arXiv:<id>;
- ignore BibTeX issue/number fields in the HTML display;
- keep the year outside the clickable journal/venue text.
"""

from __future__ import annotations

import html
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
BIB_PATH = ROOT / "data" / "ikuta.bib"
TEMPLATE_PATH = ROOT / "templates" / "publications.template.html"
OUTPUT_PATH = ROOT / "publications.html"
PLACEHOLDER = "{{PUBLICATIONS}}"

STRING_MACROS = {
    "pra": "Phys. Rev. A",
    "prl": "Phys. Rev. Lett.",
}


def _balanced_value(text: str, pos: int, open_char: str, close_char: str) -> tuple[str, int]:
    """Read a braced/quoted BibTeX value starting at pos."""
    assert text[pos] == open_char
    if open_char == '"':
        i = pos + 1
        out = []
        escaped = False
        while i < len(text):
            ch = text[i]
            if ch == '"' and not escaped:
                return "".join(out), i + 1
            out.append(ch)
            escaped = (ch == "\\" and not escaped)
            if ch != "\\":
                escaped = False
            i += 1
        raise ValueError("Unterminated quoted BibTeX value")

    depth = 1
    i = pos + 1
    out = []
    while i < len(text):
        ch = text[i]
        if ch == "{" and (i == 0 or text[i - 1] != "\\"):
            depth += 1
        elif ch == "}" and (i == 0 or text[i - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise ValueError("Unterminated braced BibTeX value")


def parse_bibtex(text: str) -> list[dict[str, str]]:
    """Small BibTeX parser sufficient for this repository; preserves entry order."""
    entries: list[dict[str, str]] = []
    i = 0
    n = len(text)

    while i < n:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.match(r"@(\w+)\s*\{", text[at:])
        if not m:
            i = at + 1
            continue

        entry_type = m.group(1).lower()
        body_start = at + m.end() - 1  # points at opening {
        body, next_pos = _balanced_value(text, body_start, "{", "}")
        i = next_pos

        comma = body.find(",")
        if comma < 0:
            continue
        key = body[:comma].strip()
        fields_text = body[comma + 1 :]
        fields: dict[str, str] = {"ENTRYTYPE": entry_type, "ID": key}

        p = 0
        L = len(fields_text)
        while p < L:
            while p < L and (fields_text[p].isspace() or fields_text[p] == ","):
                p += 1
            if p >= L:
                break

            name_match = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*", fields_text[p:])
            if not name_match:
                # Skip an unrecognized fragment up to the next comma.
                next_comma = fields_text.find(",", p)
                if next_comma < 0:
                    break
                p = next_comma + 1
                continue

            name = name_match.group(1).lower()
            p += name_match.end()
            if p >= L:
                fields[name] = ""
                break

            if fields_text[p] == "{":
                value, p = _balanced_value(fields_text, p, "{", "}")
            elif fields_text[p] == '"':
                value, p = _balanced_value(fields_text, p, '"', '"')
            else:
                start = p
                while p < L and fields_text[p] not in ",\n\r":
                    p += 1
                value = fields_text[start:p].strip()

            fields[name] = value.strip()

        entries.append(fields)

    return entries


def strip_outer_braces(value: str) -> str:
    value = value.strip()
    changed = True
    while changed and len(value) >= 2 and value[0] == "{" and value[-1] == "}":
        changed = False
        depth = 0
        valid = True
        for idx, ch in enumerate(value):
            if ch == "{" and (idx == 0 or value[idx - 1] != "\\"):
                depth += 1
            elif ch == "}" and (idx == 0 or value[idx - 1] != "\\"):
                depth -= 1
                if depth == 0 and idx != len(value) - 1:
                    valid = False
                    break
        if valid and depth == 0:
            value = value[1:-1].strip()
            changed = True
    return value


_ACCENT_MAP = {
    ('"', 'A'): 'Ä', ('"', 'a'): 'ä', ('"', 'E'): 'Ë', ('"', 'e'): 'ë',
    ('"', 'I'): 'Ï', ('"', 'i'): 'ï', ('"', 'O'): 'Ö', ('"', 'o'): 'ö',
    ('"', 'U'): 'Ü', ('"', 'u'): 'ü', ('"', 'Y'): 'Ÿ', ('"', 'y'): 'ÿ',
    ("'", 'A'): 'Á', ("'", 'a'): 'á', ("'", 'E'): 'É', ("'", 'e'): 'é',
    ("'", 'I'): 'Í', ("'", 'i'): 'í', ("'", 'O'): 'Ó', ("'", 'o'): 'ó',
    ("'", 'U'): 'Ú', ("'", 'u'): 'ú', ("'", 'Y'): 'Ý', ("'", 'y'): 'ý',
    ('`', 'A'): 'À', ('`', 'a'): 'à', ('`', 'E'): 'È', ('`', 'e'): 'è',
    ('`', 'I'): 'Ì', ('`', 'i'): 'ì', ('`', 'O'): 'Ò', ('`', 'o'): 'ò',
    ('`', 'U'): 'Ù', ('`', 'u'): 'ù',
    ('^', 'A'): 'Â', ('^', 'a'): 'â', ('^', 'E'): 'Ê', ('^', 'e'): 'ê',
    ('^', 'I'): 'Î', ('^', 'i'): 'î', ('^', 'O'): 'Ô', ('^', 'o'): 'ô',
    ('^', 'U'): 'Û', ('^', 'u'): 'û',
    ('~', 'A'): 'Ã', ('~', 'a'): 'ã', ('~', 'N'): 'Ñ', ('~', 'n'): 'ñ',
    ('~', 'O'): 'Õ', ('~', 'o'): 'õ',
    ('v', 'C'): 'Č', ('v', 'c'): 'č', ('v', 'S'): 'Š', ('v', 's'): 'š',
    ('v', 'Z'): 'Ž', ('v', 'z'): 'ž',
    ('c', 'C'): 'Ç', ('c', 'c'): 'ç', ('c', 'S'): 'Ş', ('c', 's'): 'ş',
    ('c', 'T'): 'Ţ', ('c', 't'): 'ţ',
}


def latex_to_text(value: str) -> str:
    """Convert the limited LaTeX used in the bibliography to readable Unicode."""
    value = strip_outer_braces(value)

    # Common escaped punctuation and simple math commands.
    value = value.replace(r"\&", "&").replace(r"\_", "_")
    value = value.replace(r"\%", "%")
    value = value.replace(r"\times", "×")
    value = value.replace(r"\textendash", "–")
    value = value.replace(r"\textemdash", "—")

    # Accent forms such as {\"O}, {\c{S}}, {\v{s}}, {\'e}.
    accent_pat = re.compile(r"\{?\\([\"'`^~vc])\s*\{?([A-Za-z])\}?\}?")

    def accent_repl(match: re.Match[str]) -> str:
        accent, char = match.group(1), match.group(2)
        return _ACCENT_MAP.get((accent, char), char)

    old = None
    while old != value:
        old = value
        value = accent_pat.sub(accent_repl, value)

    # A few common LaTeX letters.
    value = value.replace(r"\ss", "ß")
    value = value.replace(r"\ae", "æ").replace(r"\AE", "Æ")
    value = value.replace(r"\o", "ø").replace(r"\O", "Ø")

    # Remove math delimiters and remaining grouping braces.
    value = value.replace("$", "")
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"\\([A-Za-z]+)", r"\1", value)
    value = re.sub(r"\s+", " ", value).strip()
    return unicodedata.normalize("NFC", value)


def field(entry: dict[str, str], name: str) -> str:
    value = entry.get(name, "").strip()
    if not value:
        return ""
    if name in {"journal", "booktitle"} and value.lower() in STRING_MACROS:
        return STRING_MACROS[value.lower()]
    return latex_to_text(value)


def format_author(raw: str) -> str:
    raw = raw.strip()
    if raw.lower() == "others":
        return "et al."
    text = latex_to_text(raw)
    if "," in text:
        family, given = [part.strip() for part in text.split(",", 1)]
        return f"{given} {family}".strip()
    return text


def format_authors(entry: dict[str, str]) -> str:
    raw = entry.get("author", "")
    if not raw:
        return ""
    # This bibliography does not contain the word 'and' inside grouped names.
    authors = re.split(r"\s+and\s+", raw.strip())
    return ", ".join(format_author(a) for a in authors if a.strip())


def is_arxiv(entry: dict[str, str]) -> bool:
    return field(entry, "journal").lower().startswith("arxiv")


def arxiv_id(entry: dict[str, str]) -> str | None:
    journal = field(entry, "journal")
    m = re.search(r"arXiv\s*(?:preprint\s*)?arXiv\s*:\s*([^\s,]+)", journal, re.I)
    if not m:
        m = re.search(r"arXiv\s*:\s*([^\s,]+)", journal, re.I)
    return m.group(1) if m else None


def normalize_title(title: str) -> str:
    title = latex_to_text(title).casefold()
    return "".join(ch for ch in title if ch.isalnum())


PROCEEDINGS_ENTRY_TYPES = {"inproceedings", "proceedings", "conference"}


def remove_proceedings(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Exclude conference/proceedings entries from the web publication list.

    The BibTeX entries themselves are left untouched. Book chapters
    (@incollection) are retained.
    """
    return [
        entry
        for entry in entries
        if entry.get("ENTRYTYPE", "").lower() not in PROCEEDINGS_ENTRY_TYPES
    ]


def remove_duplicate_arxiv(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    published_titles = {
        normalize_title(e.get("title", ""))
        for e in entries
        if not is_arxiv(e) and e.get("title")
    }
    return [
        e for e in entries
        if not (is_arxiv(e) and normalize_title(e.get("title", "")) in published_titles)
    ]


def link_for(entry: dict[str, str]) -> str:
    aid = arxiv_id(entry)
    if aid:
        return f"https://arxiv.org/abs/{aid}"
    doi = field(entry, "doi")
    if doi:
        if doi.lower().startswith(("http://", "https://")):
            return doi
        return f"https://doi.org/{doi}"
    return field(entry, "url")


def venue_text(entry: dict[str, str]) -> str:
    aid = arxiv_id(entry)
    if aid:
        return f"arXiv:{aid}"

    venue = field(entry, "journal") or field(entry, "booktitle")
    volume = field(entry, "volume")
    pages = field(entry, "pages").replace("--", "–")

    text = venue
    if volume:
        text += f" {volume}"
    if pages:
        text += f", {pages}"
    return text.strip()


def render_entry(entry: dict[str, str]) -> str:
    authors = html.escape(format_authors(entry))
    title = html.escape(field(entry, "title"), quote=True)
    venue = html.escape(venue_text(entry), quote=True)
    year = html.escape(field(entry, "year"))
    href = link_for(entry)

    if href:
        venue_html = (
            f'<a class="item-link" href="{html.escape(href, quote=True)}">'
            f"{venue}</a>"
        )
    else:
        venue_html = venue

    return f'<li>{authors}, &quot;{title}&quot;, {venue_html} ({year}).</li>'


def render_publications(entries: list[dict[str, str]]) -> str:
    entries = remove_proceedings(entries)
    entries = remove_duplicate_arxiv(entries)

    # Stable sort: Python's sort preserves BibTeX order for equal years.
    def year_num(entry: dict[str, str]) -> int:
        try:
            return int(field(entry, "year"))
        except ValueError:
            return -1

    entries = sorted(entries, key=year_num, reverse=True)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    year_order: list[str] = []
    for entry in entries:
        year = field(entry, "year") or "Other"
        if year not in grouped:
            year_order.append(year)
        grouped[year].append(entry)

    sections = []
    for year in year_order:
        items = "".join(render_entry(e) for e in grouped[year])
        sections.append(
            f'<section class="year-section"><h2>{html.escape(year)}</h2>'
            f'<ol class="entries">{items}</ol></section>'
        )
    return "\n".join(sections)


def main() -> None:
    bib_text = BIB_PATH.read_text(encoding="utf-8")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"Missing placeholder {PLACEHOLDER!r} in {TEMPLATE_PATH.name}")

    entries = parse_bibtex(bib_text)
    body = render_publications(entries)
    output = template.replace(PLACEHOLDER, body)
    OUTPUT_PATH.write_text(output, encoding="utf-8")

    without_proceedings = remove_proceedings(entries)
    kept_entries = remove_duplicate_arxiv(without_proceedings)
    proceedings_count = len(entries) - len(without_proceedings)
    duplicate_arxiv_count = len(without_proceedings) - len(kept_entries)

    details = [f"excluded {proceedings_count} proceedings/conference entries"]
    if duplicate_arxiv_count:
        details.append(f"{duplicate_arxiv_count} duplicate arXiv entries")

    print(
        f"Generated {OUTPUT_PATH.name}: {len(kept_entries)} publications "
        f"from {len(entries)} BibTeX entries "
        f"({', '.join(details)})"
    )


if __name__ == "__main__":
    main()
