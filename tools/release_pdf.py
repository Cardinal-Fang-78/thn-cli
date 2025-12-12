from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from thn_cli import __version__

import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: release_pdf.py OUTPUT")

    output = sys.argv[1]
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(output, pagesize=LETTER)

    story = []

    title = f"THN CLI Release Report\nVersion {__version__}"
    story.append(Paragraph(title, styles['Title']))

    body = """
    This automated release document summarizes the build outputs,
    test suite results, and metadata for this THN CLI distribution.
    """

    story.append(Paragraph(body, styles['BodyText']))

    doc.build(story)
    print(f"PDF generated: {output}")

if __name__ == "__main__":
    main()
