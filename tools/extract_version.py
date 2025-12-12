import pathlib
import re
import sys

path = pathlib.Path("thn_cli/__init__.py")

text = path.read_text(encoding="utf-8")

match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)

if not match:
    print("ERROR: __version__ not found", file=sys.stderr)
    sys.exit(1)

version = match.group(1)

print(f"file_version={version}")
print(f"::set-output name=file_version::{version}")
