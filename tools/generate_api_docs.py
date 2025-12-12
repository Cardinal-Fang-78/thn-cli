import os
from pathlib import Path
import pydoc

PACKAGE = "thn_cli"
OUTPUT = Path("docs/api")

OUTPUT.mkdir(parents=True, exist_ok=True)

modules = []

for root, dirs, files in os.walk(PACKAGE):
    for file in files:
        if file.endswith(".py") and file != "__main__.py":
            mod_path = Path(root) / file
            mod = str(mod_path).replace("/", ".").replace("\\", ".")[:-3]
            modules.append(mod)

for mod in sorted(modules):
    html = pydoc.HTMLDoc().page(mod, pydoc.render_doc(mod, "Help on %s"))
    out = OUTPUT / f"{mod}.html"
    out.write_text(html, encoding="utf-8")
    print(f"Generated {out}")
