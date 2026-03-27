# Smoke Test

## Ticket

- EXEC-008

## Overall Result

Overall Result: FAIL

## Notes

The smoke-test run stopped on the first failing command. Inspect the recorded output before closeout.

## Commands

### 1. python compileall

- reason: Detected uv.lock; using repo-managed uv runtime; generic Python syntax smoke check
- command: `uv run python -m compileall -q -x (^|/)(\.git|\.opencode|node_modules|dist|build|out|venv|\.venv|__pycache__)(/|$) .`
- exit_code: 0
- duration_ms: 130

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. acceptance command 1

- reason: Ticket acceptance criteria define an explicit smoke-test command.
- command: `uv run pytest tests/hub/test_security.py -q --tb=no`
- exit_code: 1
- duration_ms: 2004

#### stdout

~~~~text
F..........................                                              [100%]
=========================== short test summary info ============================
FAILED tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected
1 failed, 26 passed in 0.99s
~~~~

#### stderr

~~~~text
<no output>
~~~~
