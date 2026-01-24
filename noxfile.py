import nox

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.14"]


# ---------------------------------------------------------------------------
# Test / Quality Sessions (authoritative execution contexts)
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.install("pytest", "pytest-cov", "coverage")
    session.install("-e", ".")
    session.run(
        "pytest",
        "--cov=thn_cli",
        "--cov-report=xml",
        "--cov-report=term",
    )


@nox.session
def lint(session):
    session.install("flake8")
    session.env["PYTHONPATH"] = "."
    session.run("flake8", "thn_cli")


@nox.session
def typing(session):
    session.install("mypy")
    session.env["PYTHONPATH"] = "."
    session.run("mypy", "thn_cli")


# ---------------------------------------------------------------------------
# Developer Verification Sessions (read-only, non-authoritative)
# ---------------------------------------------------------------------------


@nox.session(name="verify-cli-inventory", python=False)
def verify_cli_inventory(session):
    """
    Developer-only check.
    Verifies CLI registry ↔ inventory documentation parity.
    """
    session.env["PYTHONPATH"] = "."
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
    session.env["PYTHONPATH"] = "."
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
    session.env["PYTHONPATH"] = "."
    session.run(
        "python",
        "scripts/verify_cli_domain_separation.py",
        external=True,
    )


@nox.session(name="verify-dev-tooling-inventory", python=False)
def verify_dev_tooling_inventory(session):
    """
    Developer-only check.
    Verifies scripts/ ↔ DEV_TOOLING_INVENTORY.md parity.
    """
    session.env["PYTHONPATH"] = "."
    session.run(
        "python",
        "scripts/verify_dev_tooling_inventory.py",
        external=True,
    )


# ---------------------------------------------------------------------------
# Aggregate Developer Audits
# ---------------------------------------------------------------------------


@nox.session(name="audit", python=False)
def audit(session):
    """
    Developer-only audit umbrella.

    Runs all non-authoritative verification tools to detect
    documentation, inventory, and domain drift.
    """
    session.run("nox", "-s", "verify-cli-inventory", external=True)
    session.run("nox", "-s", "verify-dev-tooling-inventory", external=True)
    session.run("nox", "-s", "verify-cli-domain-separation", external=True)
    session.run("nox", "-s", "verify-diagnostic-purity", external=True)


@nox.session(name="hygiene", python=False)
def hygiene(session):
    """
    Developer hygiene umbrella.

    Includes:
    - CLI inventory verification
    - DEV tooling inventory verification
    - Shell artifact (junk file) detection in strict mode
    """
    session.run("nox", "-s", "verify-cli-inventory", external=True)
    session.run("nox", "-s", "verify-dev-tooling-inventory", external=True)

    session.env["PYTHONPATH"] = "."
    session.run(
        "python",
        "scripts/forbid_zero_byte_no_ext.py",
        "--strict",
        external=True,
    )
