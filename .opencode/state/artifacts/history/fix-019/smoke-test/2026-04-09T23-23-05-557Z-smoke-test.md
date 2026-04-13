# Smoke Test

## Ticket

- FIX-019

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `uv run python -m py_compile src/hub/main.py src/hub/lifespan.py`
- exit_code: 0
- duration_ms: 84
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `uv run python -c from src.hub.main import app; print(app)`
- exit_code: 0
- duration_ms: 1977
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
<fastapi.applications.FastAPI object at 0x736fce8a7680>
~~~~

#### stderr

~~~~text
<no output>
~~~~
