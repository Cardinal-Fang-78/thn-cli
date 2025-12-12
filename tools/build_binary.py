import PyInstaller.__main__
import pathlib

HERE = pathlib.Path(__file__).parent
ENTRY = HERE.parent / "thn_cli" / "__main__.py"

PyInstaller.__main__.run([
    str(ENTRY),
    "--name=thn",
    "--onefile",
    "--clean",
])
