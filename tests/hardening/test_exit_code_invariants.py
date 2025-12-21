from thn_cli.__main__ import main


def test_help_exits_zero():
    assert main(["--help"]) == 0


def test_version_exits_zero():
    assert main(["--version"]) == 0


def test_invalid_command_exits_user_error():
    assert main(["definitely-not-a-command"]) == 1


def test_missing_command_exits_user_error():
    assert main([]) == 1
