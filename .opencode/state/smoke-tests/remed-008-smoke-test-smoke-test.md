# Smoke Test

## Ticket

- REMED-008

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.lifespan import lifespan; print('OK')`
- exit_code: 0
- duration_ms: 4184
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
OK
~~~~

#### stderr

~~~~text
   Building gpttalker @ file:///home/pc/projects/GPTTalker
      Built gpttalker @ file:///home/pc/projects/GPTTalker
Uninstalled 1 package in 17ms
Installed 1 package in 2ms
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.main import app; print('OK')`
- exit_code: 0
- duration_ms: 2332
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

### 3. command override 3

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.node_agent.main import app; print('OK')`
- exit_code: 0
- duration_ms: 836
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

### 4. command override 4

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.services.node_client import HubNodeClient; from src.node_agent.executor import OperationExecutor; print('OK')`
- exit_code: 0
- duration_ms: 2340
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

### 5. command override 5

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.lifespan import lifespan; from src.hub.mcp import MCPProtocolHandler; print('OK')`
- exit_code: 0
- duration_ms: 2116
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
