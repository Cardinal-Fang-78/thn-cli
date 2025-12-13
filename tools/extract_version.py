import re
import sys
from pathlib import Path

INIT_FILE = Path("thn_cli/__init__.py")

if not INIT_FILE.exists():
    print("ERROR: thn_cli/__init__.py not found", file=sys.stderr)
    sys.exit(1)

text = INIT_FILE.read_text(encoding="utf-8")

match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)

if not match:
    print("ERROR: __version__ not found in thn_cli/__init__.py", file=sys.stderr)
    sys.exit(1)

# IMPORTANT:
# Print ONLY the version string, no labels, no GitHub directives
print(match.group(1))
