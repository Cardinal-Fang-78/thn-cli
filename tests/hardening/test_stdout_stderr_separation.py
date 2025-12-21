from thn_cli.__main__ import main


def run_and_capture(argv, capsys):
    try:
        code = main(argv)
    except SystemExit:
        code = -999
    out = capsys.readouterr()
    return code, out.out, out.err


def test_help_writes_only_stdout(capsys):
    code, out, err = run_and_capture(["--help"], capsys)
    assert code == 0
    assert out.strip()
    assert err == ""


def test_version_writes_only_stdout(capsys):
    code, out, err = run_and_capture(["--version"], capsys)
    assert code == 0
    assert out.strip()
    assert err == ""


def test_invalid_command_writes_only_stderr(capsys):
    code, out, err = run_and_capture(["nope"], capsys)
    assert code == 1
    assert out == ""
    assert err.strip()
