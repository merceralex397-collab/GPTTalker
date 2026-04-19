# Smoke Test

## Ticket

- REMED-018

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.main import app; print("hub OK")`
- exit_code: 0
- duration_ms: 1884
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
hub OK
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.node_agent.main import app; print("node OK")`
- exit_code: 0
- duration_ms: 563
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
node OK
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 3. command override 3

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.shared.migrations import run_migrations; print("migrations OK")`
- exit_code: 0
- duration_ms: 300
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
migrations OK
~~~~

#### stderr

~~~~text
<no output>
~~~~
