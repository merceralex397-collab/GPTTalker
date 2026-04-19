# Smoke Test

## Ticket

- REMED-022

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.main import app; print('OK')`
- exit_code: 0
- duration_ms: 1197
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
OK
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.node_agent.main import app; print('OK')`
- exit_code: 0
- duration_ms: 407
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
OK
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 3. command override 3

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.shared.migrations import run_migrations; print('OK')`
- exit_code: 0
- duration_ms: 212
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
OK
~~~~

#### stderr

~~~~text
<no output>
~~~~
