# Smoke Test

## Ticket

- EXEC-013

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override

- reason: Explicit smoke-test command override supplied by the caller.
- command: `uv run ruff check --select UP017 src/hub/services/node_health.py && uv run ruff check --select UP035 tests/conftest.py && uv run ruff check --select UP041 src/hub/services/tunnel_manager.py`
- exit_code: 0
- duration_ms: 46

#### stdout

~~~~text
All checks passed!
~~~~

#### stderr

~~~~text
warning: Failed to lint uv: No such file or directory (os error 2)
warning: Failed to lint &&: No such file or directory (os error 2)
warning: Failed to lint ruff: No such file or directory (os error 2)
warning: Failed to lint check: No such file or directory (os error 2)
warning: Failed to lint run: No such file or directory (os error 2)
~~~~
