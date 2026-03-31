# Environment Bootstrap

## Ticket

- REMED-001

## Overall Result

Overall Result: PASS

## Environment Fingerprint

- fc5f4df429c83f6c0d1731c6438994e10cbb8dcfd008a53776689fe69358c4df

## Missing Prerequisites

- None

## Notes

Dependency installation and bootstrap verification completed successfully.

## Commands

### 1. uv availability

- reason: Check whether uv is available for lockfile-based Python bootstrap.
- command: `uv --version`
- exit_code: 0
- duration_ms: 5
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
uv 0.11.2 (x86_64-unknown-linux-gnu)
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. uv sync

- reason: Sync the Python environment from uv.lock without relying on global pip.
- command: `uv sync --locked --extra dev`
- exit_code: 0
- duration_ms: 11979
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
Using CPython 3.12.3 interpreter at: /usr/bin/python3
Creating virtual environment at: .venv
Resolved 43 packages in 0.59ms
   Building gpttalker @ file:///home/rowan/GPTTalker
Downloading ruff (10.8MiB)
Downloading pygments (1.2MiB)
Downloading pydantic-core (2.0MiB)
Downloading uvloop (4.2MiB)
Downloading grpcio (6.4MiB)
Downloading numpy (15.9MiB)
 Downloaded pygments
      Built gpttalker @ file:///home/rowan/GPTTalker
 Downloaded pydantic-core
 Downloaded uvloop
 Downloaded grpcio
 Downloaded ruff
 Downloaded numpy
Prepared 41 packages in 11.90s
Installed 41 packages in 16ms
 + aiosqlite==0.22.1
 + annotated-doc==0.0.4
 + annotated-types==0.7.0
 + anyio==4.12.1
 + certifi==2026.2.25
 + click==8.3.1
 + fastapi==0.135.1
 + gpttalker==0.1.0 (from file:///home/rowan/GPTTalker)
 + grpcio==1.78.0
 + h11==0.16.0
 + h2==4.3.0
 + hpack==4.1.0
 + httpcore==1.0.9
 + httptools==0.7.1
 + httpx==0.28.1
 + hyperframe==6.1.0
 + idna==3.11
 + iniconfig==2.3.0
 + numpy==2.4.3
 + packaging==26.0
 + pluggy==1.6.0
 + portalocker==3.2.0
 + protobuf==7.34.0
 + pydantic==2.12.5
 + pydantic-core==2.41.5
 + pydantic-settings==2.13.1
 + pygments==2.19.2
 + pytest==9.0.2
 + pytest-asyncio==1.3.0
 + python-dotenv==1.2.2
 + pyyaml==6.0.3
 + qdrant-client==1.17.1
 + ruff==0.15.6
 + starlette==0.52.1
 + typing-extensions==4.15.0
 + typing-inspection==0.4.2
 + urllib3==2.6.3
 + uvicorn==0.42.0
 + uvloop==0.22.1
 + watchfiles==1.1.1
 + websockets==16.0
~~~~

### 3. project python ready

- reason: Verify the repo-local Python interpreter is available after bootstrap.
- command: `/home/rowan/GPTTalker/.venv/bin/python --version`
- exit_code: 0
- duration_ms: 1
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
Python 3.12.3
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 4. project pytest ready

- reason: Verify the repo-local pytest executable is available for validation work.
- command: `/home/rowan/GPTTalker/.venv/bin/pytest --version`
- exit_code: 0
- duration_ms: 354
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
pytest 9.0.2
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 5. project ruff ready

- reason: Verify the repo-local ruff executable is still available after bootstrap sync.
- command: `/home/rowan/GPTTalker/.venv/bin/ruff --version`
- exit_code: 0
- duration_ms: 2
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
ruff 0.15.6
~~~~

#### stderr

~~~~text
<no output>
~~~~
