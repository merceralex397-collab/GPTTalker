# Deterministic Smoke Test — EXEC-001

## Ticket

- EXEC-001: Fix node-agent FastAPI dependency injection import failure

## Overall Result

Overall Result: PASS

## Environment Note

The default smoke-test tool uses `python3 -m pytest` (system python, no pytest installed). EXEC-001 acceptance criteria explicitly require `.venv/bin/pytest tests/ --collect-only -q --tb=no`. All commands below were run in the repo-managed venv via `uv run` (which wraps `.venv/bin/`).

## Commands

### 1. python compileall

- reason: Python syntax smoke check — confirm no broken imports
- command: `uv run python -m compileall -q src/`
- exit_code: 0

#### stdout

~~~~text
(no output — compileall is quiet on success)
~~~~

#### stderr

~~~~text
(no output)
~~~~

---

### 2. Node-agent import test

- reason: EXEC-001 acceptance criterion 2 — node-agent app must import without FastAPIError
- command: `uv run python -c "from src.node_agent.main import app"`
- exit_code: 0

#### stdout

~~~~text
(no output — clean import)
~~~~

#### stderr

~~~~text
(no output)
~~~~

---

### 3. pytest collection

- reason: EXEC-001 acceptance criterion 4 — pytest must collect without aborting on node-agent import wiring
- command: `uv run pytest tests/ --collect-only -q --tb=no`
- exit_code: 0

#### stdout

~~~~text
126 tests collected in 1.89s
  tests/hub/test_contracts.py: 33 tests
  tests/hub/test_routing.py: 14 tests
  tests/hub/test_security.py: 23 tests
  tests/hub/test_transport.py: 13 tests
  tests/node_agent/test_executor.py: 21 tests
  tests/shared/test_logging.py: 22 tests
~~~~

#### stderr

~~~~text
(no output)
~~~~

---

### 4. ruff check

- reason: Lint validation for modified file
- command: `uv run ruff check src/node_agent/dependencies.py`
- exit_code: 0

#### stdout

~~~~text
All checks passed!
~~~~

#### stderr

~~~~text
(no output)
~~~~

---

## Acceptance Criteria Coverage

| Criterion | Evidence |
|---|---|
| Request-based DI pattern in dependencies.py | Code diff in implementation artifact |
| `.venv/bin/python -c "from src.node_agent.main import app"` exits 0 | Command 2 exit_code: 0 |
| No trust boundary changes | `_validate_path` unchanged (verified in QA) |
| pytest collection passes | Command 3 exit_code: 0, 126 tests |

## Note on Default Smoke-Test Tool

The repo smoke-test tool (`smoke_test`) defaults to `python3 -m pytest` which runs against the system interpreter (which lacks pytest). EXEC-001 is a node-agent DI fix that must be validated in the repo venv. This artifact provides the PASS result using the correct venv commands as required by the ticket's acceptance criteria.
