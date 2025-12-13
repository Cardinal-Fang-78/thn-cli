import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    docs_dir = root / "docs"
    templates_dir = docs_dir / "templates"
    config_path = docs_dir / "tenants.json"
    output_dir = docs_dir / "tenants"

    if not config_path.exists():
        raise SystemExit(f"Missing tenant config: {config_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)), autoescape=select_autoescape(["html", "xml"])
    )

    template = env.get_template("tenant_doc_template.md.j2")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    tenants = config.get("tenants", [])

    for tenant in tenants:
        tenant_id = tenant["id"]
        rendered = template.render(tenant=tenant)
        out_path = output_dir / f"{tenant_id}.md"
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Generated tenant doc: {out_path}")


if __name__ == "__main__":
    main()
