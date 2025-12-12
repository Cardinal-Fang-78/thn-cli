from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

POLICY_MD = Path("docs/THN_Versioning_Policy.md")
OUTPUT = Path("docs/pdfs/THN_Versioning_Policy.pdf")


def draw_markdown_lines(c, text, start_y):
    """
    Very simple Markdown→PDF rendering:
    - headers → larger font
    - lists → indent
    - normal text → body font
    """
    y = start_y
    for line in text.splitlines():
        stripped = line.strip()

        # Section headers
        if stripped.startswith("# "):
            c.setFont("Helvetica-Bold", 16)
            c.drawString(0.75 * inch, y, stripped[2:])
            y -= 0.30 * inch
            continue

        if stripped.startswith("## "):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(0.75 * inch, y, stripped[3:])
            y -= 0.26 * inch
            continue

        # Bullets
        if stripped.startswith("- "):
            c.setFont("Helvetica", 10)
            c.drawString(1.0 * inch, y, "• " + stripped[2:])
            y -= 0.18 * inch
            continue

        # Normal content
        c.setFont("Helvetica", 10)
        c.drawString(0.75 * inch, y, stripped)
        y -= 0.18 * inch

    return y


def main():
    if not POLICY_MD.exists():
        raise SystemExit("Policy file not found")

    text = POLICY_MD.read_text(encoding="utf-8")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=LETTER)

    # Dark THN background
    width, height = LETTER
    c.setFillColorRGB(0.266, 0.266, 0.266)   # #444444
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setFillColorRGB(0.92, 0.92, 0.92)

    y = height - 0.75 * inch
    y = draw_markdown_lines(c, text, y)

    c.showPage()
    c.save()

    print(f"Generated PDF: {OUTPUT}")


if __name__ == "__main__":
    main()
