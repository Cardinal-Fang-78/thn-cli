# THN CLI Development Makefile

.PHONY: dev test lint format clean dist

# Install developer dependencies
dev:
	pip install -e .[dev]

# Run pytest with coverage
test:
	pytest --cov=thn_cli --cov-report=term-missing

# Lint via flake8 + mypy
lint:
	flake8 thn_cli
	mypy thn_cli

# Auto-format using black + isort
format:
	black thn_cli tests
	isort thn_cli tests

# Remove build artifacts
clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache

# Build distribution
dist:
	python -m build
