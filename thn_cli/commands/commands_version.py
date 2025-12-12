"""
Version Command for THN CLI

Provides:
    • Current version display
    • Planned version transition summary
    • Guidance for changelog & release actions
"""

from __future__ import annotations
import click
from thn_cli import __version__


@click.group(help="Version and release utilities")
def version():
    pass


@version.command("show", help="Display the current THN CLI version")
def version_show():
    click.echo(f"THN CLI Version: {__version__}")


@version.command("plan", help="Show guidance for updating the version")
@click.option("--type", type=click.Choice(["major", "minor", "patch"]), required=False)
def version_plan(type: str | None):
    if type is None:
        click.echo("Specify --type major|minor|patch for recommendations.")
        return

    if type == "major":
        click.echo("MAJOR version upgrade guidance:")
        click.echo("- Breaking changes detected")
        click.echo("- Update __version__")
        click.echo("- Update CHANGELOG.md")
        click.echo("- Run full syncv2 compatibility tests")

    elif type == "minor":
        click.echo("MINOR version upgrade guidance:")
        click.echo("- Backwards-compatible new features")
        click.echo("- Update __version__")
        click.echo("- Update CHANGELOG.md")

    elif type == "patch":
        click.echo("PATCH version upgrade guidance:")
        click.echo("- Bug fixes or internal improvements")
        click.echo("- Update __version__")


COMMAND = version
