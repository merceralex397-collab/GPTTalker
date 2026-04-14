# Smoke Test

## Ticket

- REMED-011

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. python compileall

- reason: Detected uv.lock; using repo-managed uv runtime; generic Python syntax smoke check
- command: `uv run python -m compileall -q -x (^|/)(\.git|\.opencode|node_modules|dist|build|out|venv|\.venv|__pycache__)(/|$) .`
- exit_code: 0
- duration_ms: 273
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

### 2. pytest

- reason: Detected uv.lock; using repo-managed uv runtime; detected Python test surface
- command: `uv run python -m pytest`
- exit_code: 0
- duration_ms: 2900
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/pc/projects/GPTTalker
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
testpaths: tests
plugins: asyncio-1.3.0, anyio-4.12.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 131 items

tests/hub/test_contracts.py ................................             [ 24%]
tests/hub/test_routing.py ..............                                 [ 35%]
tests/hub/test_security.py ...........................                   [ 55%]
tests/hub/test_transport.py .............                                [ 65%]
tests/hub/test_tunnel_manager.py ....                                    [ 68%]
tests/node_agent/test_executor.py ......................                 [ 85%]
tests/shared/test_logging.py ...................                         [100%]

============================= 131 passed in 1.59s ==============================
~~~~

#### stderr

~~~~text
<no output>
~~~~
