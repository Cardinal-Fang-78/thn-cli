import nox

# Python versions you want to test against
PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.install("pytest", "pytest-cov")
    session.install("-e", ".")
    session.run("pytest", "--cov=thn_cli", "--cov-report=term-missing")


@nox.session
def lint(session):
    session.install("flake8", "mypy")
    session.install("-e", ".")
    session.run("flake8", "thn_cli")
    session.run("mypy", "thn_cli")


@nox.session
def format(session):
    session.install("black", "isort")
    session.run("black", "thn_cli", "tests")
    session.run("isort", "thn_cli", "tests")


@nox.session
def build(session):
    session.install("build")
    session.run("python", "-m", "build")
