from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

POLICY_MD = Path("docs/THN_Versioning_Policy.md")
OUTPUT = Path("docs/pdfs/THN_Versioning_Policy.pdf")


# ---------------------------------------------------------------------------
# Page background (dark mode)
# ---------------------------------------------------------------------------


def draw_page_background(canvas, doc):
    width, height = LETTER
    canvas.saveState()

    # THN dark background (#444444)
    canvas.setFillColorRGB(0.266, 0.266, 0.266)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Markdown → Flowables (minimal, controlled)
# ---------------------------------------------------------------------------


def markdown_to_flowables(text):
    styles = getSampleStyleSheet()

    body = ParagraphStyle(
        "THNBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor="#E6E6E6",
        leading=14,
        spaceAfter=8,
    )

    h1 = ParagraphStyle(
        "THNH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor="#FFFFFF",
        spaceAfter=14,
    )

    h2 = ParagraphStyle(
        "THNH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor="#FFFFFF",
        spaceAfter=12,
    )

    bullet = ParagraphStyle(
        "THNBullet",
        parent=body,
        leftIndent=14,
    )

    flowables = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if not line:
            flowables.append(Spacer(1, 6))
            continue

        if line.startswith("# "):
            flowables.append(Paragraph(line[2:], h1))
            continue

        if line.startswith("## "):
            flowables.append(Paragraph(line[3:], h2))
            continue

        if line.startswith("- "):
            flowables.append(Paragraph("• " + line[2:], bullet))
            continue

        flowables.append(Paragraph(line, body))

    return flowables


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if not POLICY_MD.exists():
        raise SystemExit("Policy file not found")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    text = POLICY_MD.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    flowables = markdown_to_flowables(text)

    doc.build(
        flowables,
        onFirstPage=draw_page_background,
        onLaterPages=draw_page_background,
    )

    print(f"Generated PDF: {OUTPUT}")


if __name__ == "__main__":
    main()
