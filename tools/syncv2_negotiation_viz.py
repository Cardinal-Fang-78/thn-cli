import json
from pathlib import Path
from typing import List, Dict


def load_events(path: Path) -> List[Dict]:
    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def render_html(events: List[Dict]) -> str:
    rows = []
    for ev in events:
        phase = ev.get("phase", "")
        step = ev.get("step", "")
        ts = ev.get("timestamp", "")
        detail = ev.get("detail", "")
        rows.append(
            f"<tr>"
            f"<td>{ts}</td>"
            f"<td>{phase}</td>"
            f"<td>{step}</td>"
            f"<td>{detail}</td>"
            f"</tr>"
        )

    table_rows = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>THN Sync V2 – Negotiation Visualization</title>
<style>
body {{
    background-color: #222;
    color: #f0f0f0;
    font-family: sans-serif;
}}
table {{
    border-collapse: collapse;
    width: 100%;
}}
th, td {{
    border: 1px solid #555;
    padding: 4px 8px;
    font-size: 13px;
}}
th {{
    background-color: #333;
}}
tr:nth-child(even) {{
    background-color: #2b2b2b;
}}
</style>
</head>
<body>
<h1>THN Sync V2 – Negotiation Timeline</h1>
<table>
<thead>
<tr>
<th>Timestamp</th>
<th>Phase</th>
<th>Step</th>
<th>Detail</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>
</body>
</html>
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate HTML visualization from Sync V2 negotiation logs (JSONL)."
    )
    parser.add_argument(
        "input_log",
        help="Path to negotiation log file (JSON Lines format).",
    )
    parser.add_argument(
        "--output",
        default="docs/syncv2/negotiation.html",
        help="Output HTML path (default: docs/syncv2/negotiation.html).",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    input_path = root / args.input_log
    output_path = root / args.output

    events = load_events(input_path)
    if not events:
        raise SystemExit(f"No events loaded from {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_html(events)
    output_path.write_text(html, encoding="utf-8")
    print(f"Negotiation visualization written to {output_path}")


if __name__ == "__main__":
    main()
