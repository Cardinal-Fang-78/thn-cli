import datetime
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: update_changelog.py VERSION")
    sys.exit(1)

VERSION = sys.argv[1]
today = datetime.date.today().isoformat()

changelog = Path("CHANGELOG.md")

if not changelog.exists():
    changelog.write_text("# Changelog\n\n")

old = changelog.read_text()

entry = f"""
## v{VERSION} – {today}

- Automated entry (replace with real notes)
"""

changelog.write_text(old + entry)

print(f"CHANGELOG updated with version {VERSION}")
