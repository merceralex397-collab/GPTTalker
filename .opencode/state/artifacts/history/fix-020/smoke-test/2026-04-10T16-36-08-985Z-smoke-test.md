# Smoke Test

## Ticket

- FIX-020

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `uv run python -c from src.node_agent.routes import operations; print([r.path for r in operations.router.routes])`
- exit_code: 0
- duration_ms: 801
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
['/operations/list-dir', '/operations/read-file', '/operations/search', '/operations/git-status', '/operations/write-file']
~~~~

#### stderr

~~~~text
<no output>
~~~~
