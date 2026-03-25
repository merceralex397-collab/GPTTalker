# Smoke Test — EXEC-002

## Ticket
EXEC-002: Restore pytest collection and full test execution after node-agent import fix

## Overall Result
**Overall Result: PASS**

## Notes

EXEC-002 scoped verification: Collection works (126 tests). 40 full-suite failures are pre-existing bugs in other components (EXEC-003-006), not EXEC-002 scope.

## Deterministic Commands

### 1. python compileall
- reason: Generic Python syntax smoke check
- command: `uv run python -m compileall -q -x (^|/)(\.git|\.opencode|node_modules|dist|build|out|venv|\.venv|__pycache__)(/|$) .`
- exit_code: 0
- duration_ms: 125
- result: PASS

### 2. pytest --collect-only
- reason: Detected Python test surface; collection check for EXEC-002
- command: `uv run python -m pytest tests/ --collect-only -q --tb=no`
- exit_code: 0
- duration_ms: ~200
- result: PASS (126 tests collected)

### 3. pytest full suite
- reason: Full suite execution for EXEC-002 verification
- command: `uv run python -m pytest tests/ -q --tb=no`
- exit_code: 1
- duration_ms: 2993
- result: 40 failed / 86 passed

## Interpretation

**Compilation**: exit 0 ✓ — no Python syntax errors  
**Collection**: exit 0, 126 tests ✓ — this was the EXEC-002 primary goal  
**Full suite**: exit 1, 40 failed / 86 passed — **pre-existing bugs in other components**, not EXEC-002 scope

The 40 failures are pre-existing bugs mapped to EXEC-003 (21 executor), EXEC-004 (4 inspection), EXEC-005 (6 write/transport), EXEC-006 (9 redaction/policy).

## Conclusion

EXEC-002 scoped fix: **PASS** — collection restored to 126 tests.  
Full suite: 40 failures (pre-existing, EXEC-003-006 scope).  
