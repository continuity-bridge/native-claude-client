.PHONY: help install install-dev test lint format clean run

help:
	@echo "Erebos - Development Tasks"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install package in current environment"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  test         - Run test suite with coverage"
	@echo "  lint         - Run linters (black check, pylint, mypy)"
	@echo "  format       - Auto-format code with black"
	@echo "  clean        - Remove build artifacts and caches"
	@echo "  run          - Run prototype CLI"
	@echo ""

install:
	pip install --break-system-packages -e .

install-dev:
	pip install --break-system-packages -e ".[dev]"

test:
	pytest

lint:
	@echo "Running black (check only)..."
	black --check erebos tests
	@echo ""
	@echo "Running pylint..."
	pylint erebos
	@echo ""
	@echo "Running mypy..."
	mypy erebos

format:
	black erebos tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	python3 prototype_cli.py
