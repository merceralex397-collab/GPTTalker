# Validation Commands

## Quick Reference

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff linter and formatter check |
| `make test` | Run pytest test suite |
| `make validate` | Run lint + test (full validation) |
| `make install` | Install package with dev dependencies |
| `make clean` | Remove cache directories |

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

# Run with specific pytest options
pytest tests/ -v --tb=short -x
```

## CI/CD Integration

For CI pipelines, use:

```bash
# Full validation with strict options
python -m ruff check src/ tests/ scripts/ --exit-non-zero-on-change
python -m ruff format --check src/ tests/ scripts/
python -m pytest tests/ -v --tb=short
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONPATH` | `src` | Python module search path |
| `TEST_DB_URL` | `sqlite+aiosqlite:///:memory:` | Test database URL |
| `LOG_LEVEL` | `WARNING` | Logging level for tests |

## Test Organization

Tests are organized by domain:

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── hub/
│   ├── __init__.py
│   ├── test_transport.py    # MCP transport layer tests
│   └── test_routing.py      # Tool routing tests
├── node_agent/
│   ├── __init__.py
│   └── test_executor.py     # Executor tests
└── shared/
    ├── __init__.py
    └── test_logging.py      # Logging utility tests
```

## Adding New Tests

When adding new tests:

1. Place them in the appropriate domain directory (`hub`, `node_agent`, or `shared`)
2. Use the fixtures from `conftest.py` for common test setup
3. Follow the naming convention `test_*.py`
4. Include at least one assertion per test function

## Troubleshooting

### Import Errors

If you see import errors, ensure `PYTHONPATH` includes `src/`:

```bash
export PYTHONPATH=src
pytest tests/
```

### Async Test Warnings

The project uses `pytest-asyncio` with `asyncio_mode = "auto"`. Mark async test functions with `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_example():
    ...
```
