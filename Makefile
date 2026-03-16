.PHONY: help lint test validate install clean

help:
	@echo "GPTTalker validation targets:"
	@echo "  make lint      — Run ruff linter and formatter check"
	@echo "  make test      — Run pytest test suite"
	@echo "  make validate  — Run lint + test (full validation)"
	@echo "  make install   — Install package with dev dependencies"
	@echo "  make clean     — Remove __pycache__ and .pytest_cache"

install:
	uv pip install -e ".[dev]"

lint:
	python -m ruff check src/ tests/ scripts/
	python -m ruff format --check src/ tests/ scripts/

test:
	PYTHONPATH=src python -m pytest tests/ -v

validate: lint test

clean:
	rm -rf **/__pycache__ .pytest_cache tests/__pycache__ src/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
