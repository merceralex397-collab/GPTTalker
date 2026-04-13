# Smoke Test

## Ticket

- FIX-024

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.services.node_client import HubNodeClient; from src.node_agent.executor import OperationExecutor; print('OK')`
- exit_code: 0
- duration_ms: 1941
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
