.PHONY: help install test test-unit test-integration test-fast clean lint format

help:
	@echo "Available targets:"
	@echo "  make install          - Install package with dev dependencies"
	@echo "  make test             - Run all tests (unit + integration)"
	@echo "  make test-unit        - Run only unit tests (fast)"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make test-fast        - Run unit tests in parallel"
	@echo "  make clean            - Clean build artifacts and cache"
	@echo "  make lint             - Run linters (if configured)"
	@echo "  make format           - Run code formatters (if configured)"

install:
	pip install -e ".[dev]"

test:
	python -m pytest -v

test-unit:
	python -m pytest -v -m "not integration"

test-integration:
	python -m pytest -v -m integration

test-fast:
	python -m pytest -n auto -m "not integration"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf build/ dist/ .eggs/

lint:
	@echo "Add your linter commands here (e.g., ruff, flake8, mypy)"

format:
	@echo "Add your formatter commands here (e.g., black, isort)"
