from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from thn_cli import __version__


def draw_page(c: canvas.Canvas) -> None:
    width, height = LETTER

    # Dark background #444444
    c.setFillColorRGB(0.266, 0.266, 0.266)  # #444444
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # Light text
    c.setFillColorRGB(0.9, 0.9, 0.9)

    margin_x = 0.75 * inch
    y = height - 1.0 * inch

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin_x, y, "THN CLI Release Report")
    y -= 0.35 * inch

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, f"Version {__version__}")
    y -= 0.5 * inch

    # Section heading
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Summary")
    y -= 0.25 * inch

    # Body text
    c.setFont("Helvetica", 10)
    text_lines = [
        "This document summarizes the build, tests, and metadata for this release.",
        "",
        "Key sections to complete manually after generation:",
        "- Release intent and scope",
        "- Notable changes",
        "- Compatibility notes",
        "- Sync Delta / Sync V2 implications",
    ]

    for line in text_lines:
        c.drawString(margin_x, y, line)
        y -= 0.18 * inch

    # Simple bullet section (Template C-style feel)
    y -= 0.25 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Checklist")
    y -= 0.3 * inch

    c.setFont("Helvetica", 10)
    bullets = [
        "All tests passed (pytest).",
        "CLI behavior validated for primary commands.",
        "Sync V2 envelope tests executed where applicable.",
        "Docs and changelog updated.",
    ]
    for b in bullets:
        c.drawString(margin_x, y, f"\u2022 {b}")
        y -= 0.18 * inch


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate THN Template C-style release PDF (dark background)."
    )
    parser.add_argument(
        "--output",
        default="out/release_template_c.pdf",
        help="Output PDF path.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output), pagesize=LETTER)
    draw_page(c)
    c.showPage()
    c.save()
    print(f"Template C-style release PDF generated: {output}")


if __name__ == "__main__":
    main()
