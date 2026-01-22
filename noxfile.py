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


@nox.session(name="verify-diagnostic-purity", python=False)
def verify_diagnostic_purity(session):
    """
    Developer-only check.
    Ensures diagnostic CLI domains contain no execution-capable code paths.
    """
    session.run(
        "python",
        "scripts/verify_diagnostic_domain_purity.py",
        external=True,
    )


@nox.session(name="verify-cli-domain-separation", python=False)
def verify_cli_domain_separation(session):
    """
    Developer-only structural guard.
    Enforces Sync vs Delta CLI domain separation.
    """
    session.run(
        "python",
        "scripts/verify_cli_domain_separation.py",
        external=True,
    )
