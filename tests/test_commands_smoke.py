# tests/test_commands_smoke.py

from thn_cli.__main__ import build_parser, main


def _get_command_names():
    parser = build_parser()
    # argparse hides subparsers in private fields; we introspect carefully.
    subparsers_actions = [
        a for a in parser._actions if isinstance(getattr(a, "choices", None), dict)
    ]
    names = set()
    for spa in subparsers_actions:
        names.update(spa.choices.keys())
    return names


def test_core_commands_registered():
    names = _get_command_names()

    # A representative set of commands that must be present.
    required = {
        "init",
        "list",
        "make",
        "blueprint",
        "sync",
        "sync-status",
        "sync-remote",
        "delta",
        "diag",
        "keys",
        "plugins",
        "registry",
        "tasks",
        "ui",
        "hub",
        "routing",
    }

    missing = sorted(required - names)
    assert not missing, f"Missing commands: {missing}"


def test_diag_help_does_not_crash(capsys):
    # Sanity check that `thn diag --help` runs.
    code = main(["diag", "--help"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Diagnostic utilities." in captured.out
