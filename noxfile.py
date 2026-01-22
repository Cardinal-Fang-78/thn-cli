import nox

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.14"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.install("pytest", "pytest-cov", "coverage")
    session.install("-e", ".")
    session.run("pytest", "--cov=thn_cli", "--cov-report=xml", "--cov-report=term")


@nox.session
def lint(session):
    session.install("flake8")
    session.run("flake8", "thn_cli")


@nox.session
def typing(session):
    session.install("mypy")
    session.run("mypy", "thn_cli")


@nox.session(name="verify-cli-inventory", python=False)
def verify_cli_inventory(session):
    """
    Developer-only check.
    Verifies CLI registry ↔ inventory documentation parity.
    """
    session.run(
        "python",
        "scripts/verify_cli_inventory.py",
        external=True,
    )
