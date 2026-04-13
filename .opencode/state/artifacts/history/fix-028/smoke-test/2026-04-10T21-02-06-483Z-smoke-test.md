# Smoke Test

## Ticket

- FIX-028

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `uv run python -c from src.hub.lifespan import lifespan; print("OK")`
- exit_code: 0
- duration_ms: 1918
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
