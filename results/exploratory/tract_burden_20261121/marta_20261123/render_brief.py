"""Render the one-page discussion brief from the editable source."""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


HERE = Path(__file__).resolve().parent
INK = colors.HexColor("#202a33")
MUTED = colors.HexColor("#52606d")
TITLE = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=20,
                       leading=25, textColor=INK, spaceAfter=6)
DETAIL = ParagraphStyle("Detail", fontName="Helvetica", fontSize=9.5, leading=12,
                        textColor=MUTED, spaceAfter=10)
HEADING = ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=11.2,
                         leading=14, textColor=INK, spaceBefore=10, spaceAfter=4,
                         keepWithNext=True)
BODY = ParagraphStyle("Body", fontName="Helvetica", fontSize=10.8, leading=14.6,
                      textColor=INK, spaceAfter=5)
TABLE_TEXT = ParagraphStyle("Cell", parent=BODY, fontSize=9.4, leading=12,
                            spaceAfter=0, alignment=TA_LEFT)
TABLE_NUM = ParagraphStyle("Number", parent=TABLE_TEXT, alignment=TA_RIGHT)


def make_table(lines):
    content = [[v.strip() for v in line.strip("|").split("|")]
               for i, line in enumerate(lines) if i != 1]
    data = []
    for i, row in enumerate(content):
        cells = []
        for j, value in enumerate(row):
            value = escape(value)
            cells.append(Paragraph(f"<b>{value}</b>" if i == 0 else value,
                                   TABLE_TEXT if j == 0 else TABLE_NUM))
        data.append(cells)
    table = Table(data, colWidths=[115, 138, 79, 172], spaceAfter=9)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf1f5")),
        ("LINEBELOW", (0, 0), (-1, 0), .65, colors.HexColor("#87929c")),
        ("LINEBELOW", (0, 1), (-1, -1), .4, colors.HexColor("#cbd1d6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def main():
    blocks = (HERE / "MARTA_BRIEF.md").read_text(encoding="utf-8").strip().split("\n\n")
    flow = []
    for i, block in enumerate(blocks):
        if block.startswith("|"):
            flow.append(make_table(block.splitlines()))
            continue
        if i == 0:
            flow.append(Paragraph(escape(block.removeprefix("# ")), TITLE))
            continue
        if i == 1:
            flow.append(Paragraph(escape(block.replace(" | ", "  ·  ")),
                                  DETAIL))
            continue
        lines = block.splitlines()
        if lines[0].startswith("## "):
            flow.append(Paragraph(escape(lines.pop(0).removeprefix("## ")), HEADING))
        if lines:
            flow.append(Paragraph(escape(" ".join(lines)), BODY))

    destination = HERE / "MARTA_BRIEF.pdf"
    doc = SimpleDocTemplate(str(destination), pagesize=letter, leftMargin=48, rightMargin=48,
                            topMargin=43, bottomMargin=43, invariant=1, title="Which communities do deficit screens miss?")
    doc.build(flow)


if __name__ == "__main__":
    main()
