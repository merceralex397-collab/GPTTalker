# Smoke Test

## Ticket

- EXEC-011

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=line --no-header`
- exit_code: 0
- duration_ms: 2652

#### stdout

~~~~text
........................................................................ [ 56%]
.......................................................                  [100%]
127 passed in 1.50s
~~~~

#### stderr

~~~~text
<no output>
~~~~
