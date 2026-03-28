# Smoke Test

## Ticket

- EXEC-014

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- exit_code: 0
- duration_ms: 44

#### stdout

~~~~text
All checks passed!
~~~~

#### stderr

~~~~text
<no output>
~~~~
