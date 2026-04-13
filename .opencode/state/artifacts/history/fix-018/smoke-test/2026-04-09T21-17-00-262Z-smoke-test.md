# Smoke Test

## Ticket

- FIX-018

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python3 -m py_compile src/shared/tables.py src/shared/migrations.py`
- exit_code: 0
- duration_ms: 77
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
