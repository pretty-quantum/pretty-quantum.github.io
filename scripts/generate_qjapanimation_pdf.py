#!/usr/bin/env python3
"""Generate qjapanimation.pdf from data/qjapanimation.yaml."""
from __future__ import annotations

import html
from pathlib import Path
import yaml

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, PageBreak

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DATA_PATH = ROOT / "data" / "qjapanimation.yaml"
OUTPUT_PATH = ROOT / "qjapanimation.pdf"

FONT = "HeiseiKakuGo-W5"
FONT_BODY = "HeiseiMin-W3"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))
pdfmetrics.registerFont(UnicodeCIDFont(FONT_BODY))


def invariant_canvas(*args, **kwargs):
    kwargs["invariant"] = 1
    return Canvas(*args, **kwargs)


def xml(value) -> str:
    return html.escape(str(value), quote=False)


def lines_to_html(lines) -> str:
    values = [str(x) for x in (lines or []) if x not in (None, "")]
    return "<br/>".join(xml(x) for x in values) if values else "-"


def intro_para(item: dict) -> str:
    if "text" in item:
        return xml(item["text"])
    prefix = xml(item.get("prefix", ""))
    label = xml(item.get("link_text", ""))
    url = html.escape(str(item.get("url", "")), quote=True)
    suffix = xml(item.get("suffix", ""))
    return f'{prefix}<link href="{url}" color="#315f7d">{label}</link>{suffix}'


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_BODY, 7)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawRightString(landscape(A4)[0] - 10 * mm, 7 * mm, str(doc.page))
    canvas.restoreState()


def main() -> None:
    data = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {}
    page = data.get("page", {})

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=landscape(A4),
        leftMargin=9 * mm,
        rightMargin=9 * mm,
        topMargin=9 * mm,
        bottomMargin=11 * mm,
        title=str(page.get("title") or "Qjapanimation"),
        author=str(page.get("author") or ""),
    )

    title_style = ParagraphStyle(
        "title", fontName=FONT, fontSize=15, leading=20,
        textColor=colors.HexColor("#202124"), spaceAfter=4 * mm,
    )
    author_style = ParagraphStyle(
        "author", fontName=FONT_BODY, fontSize=8.5, leading=12,
        textColor=colors.HexColor("#687078"), spaceAfter=4 * mm,
    )
    intro_style = ParagraphStyle(
        "intro", fontName=FONT_BODY, fontSize=8.2, leading=12,
        leftIndent=4 * mm, firstLineIndent=-3 * mm,
        textColor=colors.HexColor("#303438"), spaceAfter=1.2 * mm,
    )
    section_style = ParagraphStyle(
        "section", fontName=FONT, fontSize=11, leading=15,
        textColor=colors.HexColor("#202124"), spaceBefore=3 * mm, spaceAfter=2 * mm,
    )
    head_style = ParagraphStyle(
        "head", fontName=FONT, fontSize=7.6, leading=10,
        textColor=colors.HexColor("#3f474d"),
    )
    year_style = ParagraphStyle(
        "year", fontName=FONT_BODY, fontSize=7.4, leading=10, alignment=1,
    )
    title_cell_style = ParagraphStyle(
        "tcell", fontName=FONT, fontSize=7.5, leading=10.5,
        textColor=colors.HexColor("#202124"),
    )
    body_style = ParagraphStyle(
        "body", fontName=FONT_BODY, fontSize=7.2, leading=10.3,
        textColor=colors.HexColor("#202124"),
    )
    note_style = ParagraphStyle(
        "note", fontName=FONT_BODY, fontSize=7.0, leading=10,
        textColor=colors.HexColor("#4d555b"),
    )
    foot_style = ParagraphStyle(
        "foot", fontName=FONT_BODY, fontSize=7.4, leading=10,
        textColor=colors.HexColor("#687078"), spaceBefore=3 * mm,
    )

    story = [
        Paragraph(xml(page.get("title", "")), title_style),
        Paragraph(xml(page.get("author", "")), author_style),
    ]
    for item in data.get("intro", []) or []:
        story.append(Paragraph("・" + intro_para(item), intro_style))
    story.append(Spacer(1, 2 * mm))

    width = landscape(A4)[0] - doc.leftMargin - doc.rightMargin
    col_widths = [16 * mm, 48 * mm, 111 * mm, width - (16 + 48 + 111) * mm]

    for index, section in enumerate(data.get("sections", []) or []):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(xml(section.get("title", "")), section_style))
        rows = [[
            Paragraph("年", head_style),
            Paragraph("タイトル", head_style),
            Paragraph("内容", head_style),
            Paragraph("備考", head_style),
        ]]
        for entry in section.get("entries", []) or []:
            rows.append([
                Paragraph(xml(entry.get("year") if entry.get("year") else "-"), year_style),
                Paragraph(xml(entry.get("title", "")), title_cell_style),
                Paragraph(lines_to_html(entry.get("content", [])), body_style),
                Paragraph(lines_to_html(entry.get("note", [])), note_style),
            ])

        table = LongTable(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f6f8")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dfe3e7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfcfd")]),
        ]))
        story.append(table)

    story.append(Paragraph(xml(page.get("footnote", "")), foot_style))
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number, canvasmaker=invariant_canvas)
    total = sum(len(s.get("entries", []) or []) for s in data.get("sections", []) or [])
    print(f"Generated qjapanimation.pdf: {total} entries")


if __name__ == "__main__":
    main()
