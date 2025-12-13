from thn_cli.__main__ import main


def test_help_prints_to_out_only(capsys):
    try:
        main(["--help"])
    except SystemExit:
        pass

    out = capsys.readouterr()
    assert out.err == ""
    assert "THN Master Control" in out.out


def test_help_lists_known_command(capsys):
    try:
        main(["--help"])
    except SystemExit:
        pass

    out = capsys.readouterr()
    assert "sync" in out.out
