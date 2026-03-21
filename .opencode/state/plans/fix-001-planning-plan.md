# Implementation Plan: FIX-001 - Fix walrus operator syntax error in opencode.py

## Ticket Summary

Fix the walrus operator syntax error on line 399 of `src/hub/tools/opencode.py` that causes a SyntaxError, blocking hub startup through the `register_all_tools()` import chain.

## Issue Analysis

The current code at line 399 uses:
```python
if scheduler_input.allow_fallback and schedule_result := getattr(
    distributed_scheduler, "_last_result", None
):
```

This is valid Python 3.8+ syntax. However, based on the ticket description claiming a syntax error, there may be an issue with how the code is structured or an edge case that's causing problems.

## Proposed Fix

The walrus operator `:=` assigns a value to a variable as part of an expression. The fallback logic needs to:
1. Check if `allow_fallback` is True
2. Get the last scheduler result from the distributed scheduler
3. If both conditions are met, try the fallback chain

The fix should convert this to explicit assignment that maintains the same logic:
```python
if scheduler_input.allow_fallback:
    schedule_result = getattr(distributed_scheduler, "_last_result", None)
    if schedule_result:
        return await _opencode_try_fallback_chain(...)
```

## Implementation Steps

1. **Read and analyze** the current code at lines 395-420 to understand the full context
2. **Identify** any actual syntax issues (run py_compile if needed)
3. **Fix** the walrus operator usage by converting to explicit assignment
4. **Verify** the fix compiles: `python3 -m py_compile src/hub/tools/opencode.py`
5. **Test** hub startup completes without SyntaxError

## Acceptance Criteria

- [ ] `python3 -m py_compile src/hub/tools/opencode.py` succeeds
- [ ] Hub startup completes without SyntaxError  
- [ ] The walrus operator logic preserves fallback behavior

## Risk Assessment

- **Risk level**: Low
- **Impact**: Blocking issue that prevents hub startup
- **Mitigation**: Simple syntax fix, no behavioral changes

## Dependencies

None - this is a standalone bugfix.
