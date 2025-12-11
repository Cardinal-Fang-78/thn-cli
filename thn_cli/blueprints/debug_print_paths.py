import os, json
from thn_cli.blueprints.resolver import resolve_blueprint

bp = resolve_blueprint("project_default")
root = bp["_root"]

paths = []

# SUPPORT BOTH OLD .files blueprints and new .templates blueprints
if "templates" in bp:
    template_list = bp["templates"]
elif "files" in bp:
    # legacy format
    template_list = [
        {"source": rel, "destination": dest}
        for dest, rel in bp["files"].items()
    ]
else:
    template_list = []

for item in template_list:
    src_rel = item["source"]
    abs_path = os.path.join(root, src_rel)

    paths.append({
        "source": src_rel,
        "absolute": abs_path,
        "exists": os.path.exists(abs_path),
        "root": root
    })

print(json.dumps(paths, indent=4))
