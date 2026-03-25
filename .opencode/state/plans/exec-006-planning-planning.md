# EXEC-006 Planning

## Ticket
EXEC-006 — Fix structured logging redaction behavior for nested payloads

## Summary
Three bugs in `src/shared/logging.py` cause 9 test failures in `test_logging.py` and `test_security.py`.

## Bug 1: `"auth"` pattern too broad

**File:** `src/shared/logging.py` line 21

**Problem:** `"auth"` is in `SENSITIVE_PATTERNS` but is too broad. When `request.auth = {"api_key": "sk-123", "token": "abc"}` is processed, the entire `request.auth` dict is replaced with `"[REDACTED]"` because `"auth" in "auth"`.

**Test that fails:** `test_sensitive_path_redaction` in `test_security.py` (line 312-313) expects `request.auth.api_key` and `request.auth.token` to be individually redacted while the parent `auth` structure is preserved.

**Fix:** Remove `"auth"` from `SENSITIVE_PATTERNS`. The test's expected patterns list does NOT include `"auth"` — only `"authorization"`. Since `"authorization"` is not a key in any test data, removing `"auth"` won't break any other test.

## Bug 2: Truncation format wrong

**File:** `src/shared/logging.py` line 60

**Current:**
```python
return data[:10000] + "...[TRUNCATED]"
```

**Expected (test_logging.py line 114):**
```python
assert result["content"].endswith("... [TRUNCATED]")  # note the space
```

**Fix:** Change to `data[:10000] + "... [TRUNCATED]"`.

## Bug 3: String values in lists not redacted

**File:** `src/shared/logging.py` lines 57-61

**Current behavior:** String handling only truncates long strings. It never checks if the string *content* contains sensitive patterns.

```python
elif isinstance(data, str):
    if len(data) > 10000:
        return data[:10000] + "...[TRUNCATED]"
    return data
```

**Problem:** `tokens = ["token1", "token2"]` should become `["[REDACTED]", "[REDACTED]"]` because the string values contain `"token"`. But current code only truncates, never redacts based on string content.

**Test that fails:** `test_redact_sensitive_list` in `test_logging.py` lines 71-87.

**Fix:** Before truncating, check if the string content contains any sensitive pattern. If so, redact the entire string:

```python
elif isinstance(data, str):
    # Check if string content contains sensitive patterns
    data_lower = data.lower()
    if any(pattern in data_lower for pattern in SENSITIVE_PATTERNS):
        return "[REDACTED]"
    # Truncate very long strings
    if len(data) > 10000:
        return data[:10000] + "... [TRUNCATED]"
    return data
```

## Implementation Plan

1. **Remove `"auth"` from `SENSITIVE_PATTERNS`** (line 21)
2. **Add string content redaction** in the string handling branch (before truncation check)
3. **Fix truncation format** from `"...[TRUNCATED]"` to `"... [TRUNCATED]"`

## Affected Tests

| Test | File | Expected Fix |
|---|---|---|
| `test_sensitive_path_redaction` | test_security.py | Remove "auth" from patterns |
| `test_redact_sensitive_long_string` | test_logging.py | Fix truncation format |
| `test_redact_sensitive_list` | test_logging.py | Add string content redaction |
| `test_redaction_patterns_defined` | test_security.py | Should still pass (only checks expected patterns are present) |

## Validation

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py tests/hub/test_security.py -k "redact" -v --tb=short
```

Expected: All redaction-related tests pass (9 currently failing in this scope should become 0).

## Files to Change

- `src/shared/logging.py`: SENSITIVE_PATTERNS, redact_sensitive() string branch, truncation format
