import subprocess
from pathlib import Path
from typing import Optional

import click

from thn_cli import __version__

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: str, cwd: Optional[Path] = None) -> int:
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=str(cwd or ROOT))
    return result.returncode


@click.group()
def cli() -> None:
    """THN Release Control – interactive helper for local release tasks."""
    pass


@cli.command()
def info() -> None:
    """Show basic release info."""
    print(f"THN CLI version: {__version__}")
    print(f"Repository root: {ROOT}")
    checklist = ROOT / "docs" / "RELEASE_CHECKLIST.md"
    print(f"Release checklist: {checklist} (exists: {checklist.exists()})")


@cli.command()
def test() -> None:
    """Run pytest."""
    code = run("pytest -q")
    if code != 0:
        print("Tests failed.")
    else:
        print("All tests passed.")


@cli.command()
def build() -> None:
    """Build sdist + wheel."""
    run("python -m pip install --upgrade build")
    code = run("python -m build")
    if code == 0:
        print("Build completed. Artifacts in dist/")
    else:
        print("Build failed.")


@cli.command()
@click.argument("new_version")
def set_version(new_version: str) -> None:
    """
    Set __version__ directly in thn_cli/__init__.py.

    Example: thn_release_tui.py set-version 2.0.1
    """
    init_path = ROOT / "thn_cli" / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    new_lines = []
    replaced = False

    for line in lines:
        if line.strip().startswith("__version__"):
            new_lines.append(f'__version__ = "{new_version}"')
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        print("No __version__ line found in __init__.py")
        return

    init_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"Updated __version__ to {new_version} in {init_path}")


@cli.command()
def checklist() -> None:
    """Print path to the release checklist."""
    checklist = ROOT / "docs" / "RELEASE_CHECKLIST.md"
    print(f"Release checklist location: {checklist}")
    if not checklist.exists():
        print("Note: checklist file does not exist yet.")


if __name__ == "__main__":
    cli()
