# Smoke Test

## Ticket

- REMED-002

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.main import app; print('hub: OK')`
- exit_code: 0
- duration_ms: 3106
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
hub: OK
~~~~

#### stderr

~~~~text
   Building gpttalker @ file:///home/pc/projects/GPTTalker
      Built gpttalker @ file:///home/pc/projects/GPTTalker
Uninstalled 1 package in 1ms
Installed 1 package in 2ms
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.node_agent.main import app; print('node_agent: OK')`
- exit_code: 0
- duration_ms: 700
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
node_agent: OK
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 3. command override 3

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c import src.shared.models; print('shared: OK')`
- exit_code: 0
- duration_ms: 346
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
shared: OK
~~~~

#### stderr

~~~~text
<no output>
~~~~
