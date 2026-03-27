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
- duration_ms: 228

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. pytest

- reason: Detected uv.lock; using repo-managed uv runtime; running ticket-scoped Python tests
- command: `uv run python -m pytest tests/hub/test_security.py`
- exit_code: 1
- duration_ms: 2635

#### stdout

~~~~text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/pc/projects/GPTTalker
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: asyncio-1.3.0, anyio-4.12.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 27 items

tests/hub/test_security.py F..........................                   [100%]

=================================== FAILURES ===================================
____________ TestPathTraversal.test_path_traversal_dotdot_rejected _____________

self = <tests.hub.test_security.TestPathTraversal object at 0x7d8125393170>

    def test_path_traversal_dotdot_rejected(self):
        """Test that .. path traversal is rejected."""
        base = "/home/user/repo"
    
        # Attempt various .. patterns
        dangerous_paths = [
            "../etc/passwd",
            "../../../../etc/passwd",
            "foo/../../../etc/passwd",
            "foo/bar/../../secrets",
            "../foo/bar",
            # "foo/..",  # REMOVED - resolves to base, not traversal
        ]
    
        for path in dangerous_paths:
>           with pytest.raises(PathTraversalError) as exc_info:
E           Failed: DID NOT RAISE <class 'src.shared.exceptions.PathTraversalError'>

tests/hub/test_security.py:56: Failed
=========================== short test summary info ============================
FAILED tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected
========================= 1 failed, 26 passed in 1.33s =========================
~~~~

#### stderr

~~~~text
<no output>
~~~~
