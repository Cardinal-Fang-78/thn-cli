def test_cli_help_invokes():
    from thn_cli.__main__ import main
    assert main(["--help"]) == 0
