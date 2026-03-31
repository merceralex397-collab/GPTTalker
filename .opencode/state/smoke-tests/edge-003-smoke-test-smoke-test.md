# Smoke Test

## Ticket

- EDGE-003

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.services import TunnelManager; print('TunnelManager imported successfully')`
- exit_code: 0
- duration_ms: 913
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
TunnelManager imported successfully
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.config import HubConfig; cfg = HubConfig(); print('ngrok_enabled:', cfg.ngrok_enabled)`
- exit_code: 0
- duration_ms: 912
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
ngrok_enabled: False
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 3. command override 3

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/services/__init__.py`
- exit_code: 0
- duration_ms: 20
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
All checks passed!
~~~~

#### stderr

~~~~text
<no output>
~~~~
