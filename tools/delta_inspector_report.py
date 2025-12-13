from pathlib import Path
from typing import Any, Dict

from thn_cli.syncv2.delta import store  # adjust if needed


def inspect_delta(delta_path: Path) -> Dict[str, Any]:
    """
    Placeholder integration point with thn_cli.syncv2.delta.store.

    Adjust this to call your actual load/inspect functions.
    """
    # Example: store.load_index(...) – replace with your real routines.
    # For now, just report basic file stats.
    size = delta_path.stat().st_size
    return {
        "path": str(delta_path),
        "size_bytes": size,
    }


def render_html(info: Dict[str, Any]) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>THN Sync Delta – Inspector Report</title>
<style>
body {{
    background-color: #222;
    color: #f0f0f0;
    font-family: sans-serif;
}}
table {{
    border-collapse: collapse;
    margin-top: 1rem;
}}
th, td {{
    border: 1px solid #555;
    padding: 4px 8px;
}}
th {{
    background-color: #333;
}}
</style>
</head>
<body>
<h1>THN Sync Delta – Inspector Report</h1>
<table>
<tr><th>Delta Path</th><td>{info.get("path", "")}</td></tr>
<tr><th>Size (bytes)</th><td>{info.get("size_bytes", "")}</td></tr>
</table>
</body>
</html>
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate HTML report for a THN Sync Delta file.")
    parser.add_argument("delta", help="Path to delta file (.delta, .thn-delta, etc.)")
    parser.add_argument(
        "--output",
        default="docs/syncv2/delta_inspector.html",
        help="Output HTML path.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    delta_path = root / args.delta
    output_path = root / args.output

    info = inspect_delta(delta_path)
    html = render_html(info)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Delta inspector report written to {output_path}")


if __name__ == "__main__":
    main()
