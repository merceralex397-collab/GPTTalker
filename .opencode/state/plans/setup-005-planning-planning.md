# Implementation Plan: SETUP-005 — Test, Lint, and Local Validation Scaffold

## 1. Scope

This ticket establishes the validation infrastructure baseline for GPTTalker. It ensures that future tickets have a predictable, documented way to run tests, lint checks, and validation scripts locally. The scope covers validation commands, test package organization, and CI/CD-ready local validation tooling.

**Ticket**: SETUP-005  
**Wave**: 0  
**Lane**: qa  
**Status**: Planning  
**Depends On**: SETUP-001  

---

## 2. Files and Systems Affected

| Category | Path | Action |
|----------|------|--------|
| Configuration | `pyproject.toml` | Extend with scripts section for validation commands |
| Configuration | `pytest.ini` | Already configured; verify completeness |
| Configuration | `ruff.toml` | Already configured; verify completeness |
| Scripts | `scripts/validate.py` | New — unified validation entrypoint |
| Scripts | `scripts/run_tests.py` | New — pytest wrapper with environment handling |
| Scripts | `scripts/run_lint.py` | New — ruff wrapper with output formatting |
| Documentation | `docs/validation.md` | New — validation commands reference |
| Tests | `tests/conftest.py` | Extend with async db, FastAPI client fixtures |
| Tests | `tests/hub/` | New — hub domain tests |
| Tests | `tests/node_agent/` | New — node-agent domain tests |
| Tests | `tests/shared/` | New — shared utilities tests |
| Makefile | `Makefile` | New — convenience targets for common tasks |

---

## 3. Implementation Steps

### Step 1: Extend pyproject.toml with scripts section

Add a `[project.scripts]` section to define CLI entrypoints for validation:

```toml
[project.scripts]
gpttalker-validate = "scripts.validate:main"
gpttalker-test = "scripts.run_tests:main"
gpttalker-lint = "scripts.run_lint:main"
```

This enables running `gpttalker-validate` after package installation.

### Step 2: Create validation scripts directory and entrypoints

Create `scripts/__init__.py` and three scripts:

- **`scripts/validate.py`**: Unified entrypoint that runs lint + tests in sequence. Exits with code 1 if any step fails.
- **`scripts/run_tests.py`**: Wrapper around `pytest` that:
  - Sets `PYTHONPATH` to include `src/`
  - Accepts optional pytest arguments (e.g., `-v`, `-k test_name`)
  - Uses the `sqlite+aiosqlite:///:memory:` test database
  - Returns pytest exit code
- **`scripts/run_lint.py`**: Wrapper around `ruff check` and `ruff format --check` that:
  - Runs ruff on `src/`, `tests/`, and `scripts/`
  - Reports errors in a consistent format
  - Returns ruff exit code

### Step 3: Organize test package layout

Create domain-specific test directories under `tests/`:

```
tests/
├── __init__.py
├── conftest.py              # existing fixtures (extend)
├── hub/
│   ├── __init__.py
│   ├── test_transport.py     # placeholder for transport tests
│   └── test_routing.py       # placeholder for routing tests
├── node_agent/
│   ├── __init__.py
│   └── test_executor.py      # placeholder for executor tests
└── shared/
    ├── __init__.py
    └── test_logging.py       # placeholder for logging tests
```

Each `__init__.py` should contain a docstring explaining the test domain.

### Step 4: Extend conftest.py fixtures

Add the following fixtures to `tests/conftest.py`:

| Fixture | Purpose |
|---------|---------|
| `async_db_session` | Provides an aiosqlite in-memory database with schema migrations for each test |
| `test_client` | Provides a FastAPI `TestClient` for hub endpoint testing |
| `mock_node_registry` | Provides a mock node registry for testing node-related flows |
| `mock_qdrant_client` | Provides a mock Qdrant client for context tests |

Example implementation pattern:

```python
@pytest.fixture
async def async_db_session():
    """Create a fresh async database session for each test."""
    async with aiosqlite.connect(":memory:") as db:
        # Apply schema creation here (import from shared.storage)
        yield db
```

### Step 5: Create Makefile with convenience targets

Create `Makefile` at repo root:

```makefile
.PHONY: help lint test validate clean install

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
	ruff check src/ tests/ scripts/
	ruff format --check src/ tests/ scripts/

test:
	PYTHONPATH=src pytest tests/ -v

validate: lint test

clean:
	rm -rf **/__pycache__ .pytest_cache tests/__pycache__
```

### Step 6: Document validation commands

Create `docs/validation.md`:

```markdown
# Validation Commands

## Quick Reference

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff linter and formatter check |
| `make test` | Run pytest test suite |
| `make validate` | Run lint + test (full validation) |
| `make install` | Install package with dev dependencies |

## Alternative Entry Points

After installing the package (`uv pip install -e ".[dev]"`):

| Command | Description |
|---------|-------------|
| `gpttalker-validate` | Unified validation (lint + tests) |
| `gpttalker-test` | Run tests with custom arguments |
| `gpttalker-lint` | Run linter with custom arguments |

## Running Specific Tests

```bash
# Run only hub tests
pytest tests/hub/ -v

# Run only tests matching a pattern
pytest -k "test_transport"

# Run with coverage
pytest --cov=src tests/

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## CI/CD Integration

For CI pipelines, use:

```bash
# Full validation with strict options
ruff check src/ tests/ scripts/ --exit-non-zero-on-change
ruff format --check src/ tests/ scripts/
pytest tests/ -v --tb=short
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONPATH` | `src` | Python module search path |
| `TEST_DB_URL` | `sqlite+aiosqlite:///:memory:` | Test database URL |
| `LOG_LEVEL` | `WARNING` | Logging level for tests |
```

---

## 4. Validation Plan

### Pre-Implementation Verification

- [ ] Confirm `pyproject.toml` has pytest, pytest-asyncio, ruff in dev dependencies
- [ ] Confirm `pytest.ini` and `ruff.toml` exist and are valid

### Post-Implementation Verification

- [ ] `make lint` runs without errors on `src/`, `tests/`, `scripts/`
- [ ] `make test` runs and discovers tests in `tests/` subdirectories
- [ ] `make validate` runs lint + test in sequence
- [ ] `gpttalker-validate` works after `uv pip install -e ".[dev]"`
- [ ] `docs/validation.md` renders correctly and documents all commands
- [ ] Test fixtures in `conftest.py` load without import errors
- [ ] Domain test directories (`tests/hub/`, `tests/node_agent/`, `tests/shared/`) are importable

### Acceptance Criteria Check

| Criterion | Verification |
|-----------|---------------|
| Validation commands are documented and wired | `docs/validation.md` exists; Makefile targets work; CLI entrypoints respond |
| Test package layout is planned | `tests/hub/`, `tests/node_agent/`, `tests/shared/` directories exist with `__init__.py` |
| Ruff and pytest expectations match the brief | `ruff check` passes; `pytest` discovers and runs tests; config aligns with AGENTS.md |

---

## 5. Risks and Assumptions

### Risks

| Risk | Mitigation |
|------|------------|
| Scripts require `uv` or `pip` to be available | Document `uv pip install` in validation docs; provide fallback instructions |
| Test fixtures may need async setup | Use `pytest-asyncio` fixtures with proper `@pytest.fixture` async patterns |
| Domain test directories may remain empty | Add at least one placeholder test file per domain to ensure discoverability |

### Assumptions

- The operator has Python 3.11+ installed
- `uv` or `pip` is available for package installation
- Future tickets (SETUP-002 through POLISH-003) will add actual test content to the domain test directories
- The validation scaffold is expected to be stable across all subsequent tickets

---

## 6. Blockers and Required User Decisions

### Blockers

None. All required configuration files (`pyproject.toml`, `pytest.ini`, `ruff.toml`) were created in SETUP-001. No architectural or provider decisions are required.

### Required User Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Use `pytest-xdist` for parallel test execution? | Yes (add to dev deps) / No | Defer to POLISH-001; baseline uses sequential execution |
| Include pre-commit hooks? | Yes (add `.pre-commit-config.yaml`) / No | Defer to later ticket; not required for validation baseline |
| Use `coverage.py` for code coverage? | Yes (add to dev deps) / No | Defer to POLISH-001; baseline focuses on test infrastructure |

---

## 7. Summary

SETUP-005 creates the validation infrastructure that all future tickets will use. It wires up documented validation commands (`make lint`, `make test`, `make validate`), organizes the test package by domain, and provides CLI entrypoints for automation. The acceptance criteria are fully addressable within this ticket's scope, and no blocking decisions remain.
