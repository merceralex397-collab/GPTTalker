# QA Verification: FIX-021 — Fix SearchRequest Missing `mode` Field

## QA Summary

**Status**: PASS

All acceptance criteria have been verified with execution evidence. The fix correctly adds the missing `mode` field to `SearchRequest` in `routes/operations.py`, resolving the `AttributeError` that would occur at runtime.

## Acceptance Criteria Verification

### Criterion 1: Add `mode` field to `SearchRequest` in `routes/operations.py` matching the model definition in `models.py`

**Status**: ✓ PASS

**Evidence**:

Source code inspection of `src/node_agent/routes/operations.py` lines 39-47:
```python
class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str
    pattern: str
    include_patterns: list[str] | None = None
    mode: str = "text"  # Search mode: text, path, or symbol
    max_results: int = 1000
    timeout: int = 60
```

The `mode` field is present at line 45, correctly positioned between `include_patterns` and `max_results`.

Comparison with `src/node_agent/models.py` lines 42-52:
```python
class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str = Field(..., description="Directory to search in")
    pattern: str = Field(..., description="Search pattern (regex)")
    include_patterns: list[str] | None = Field(
        None, description="File patterns to include (e.g., ['*.py', '*.md'])"
    )
    mode: str = Field("text", description="Search mode: text, path, or symbol")
    max_results: int = Field(1000, ge=1, le=1000, description="Maximum matches to return")
    timeout: int = Field(60, ge=1, le=120, description="Search timeout in seconds")
```

Both definitions use the same default value `"text"` and same conceptual semantics.

### Criterion 2: `mode` field defaults to `'text'` and accepts `'text'`, `'path'`, and `'symbol'` values

**Status**: ✓ PASS

**Evidence**:

1. **Default value**: The field definition shows `mode: str = "text"` — default is correctly set to `"text"`

2. **Valid values**: The search handler at lines 218-220 in `routes/operations.py` validates the mode:
```python
valid_modes = ["text", "path", "symbol"]
mode = request.mode if request.mode in valid_modes else "text"
```

This confirms the accepted values are `"text"`, `"path"`, and `"symbol"`, with fallback to `"text"` if an invalid value is provided.

### Criterion 3: Verify SearchRequest in `routes/operations.py` has mode field by running Python import command

**Status**: ✓ PASS

**Command Execution**:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.routes.operations import SearchRequest; print('Fields:', list(SearchRequest.model_fields.keys())); assert 'mode' in SearchRequest.model_fields, 'ERROR: mode field missing!'; print('SUCCESS: mode field is present')"
```

**Exit Code**: `0` ✓

**Output**:
```
Fields: ['directory', 'pattern', 'include_patterns', 'mode', 'max_results', 'timeout']
SUCCESS: mode field is present
```

The command confirms:
- `SearchRequest` can be imported from `src.node_agent.routes.operations` without errors
- The `mode` field is present in `SearchRequest.model_fields`
- All expected fields are present: directory, pattern, include_patterns, **mode**, max_results, timeout

## Runtime Impact Verification

The handler code at line 220 reads `request.mode`:
```python
mode = request.mode if request.mode in valid_modes else "text"
```

With the `mode` field now present in `SearchRequest`, this line will no longer raise `AttributeError: 'SearchRequest' object has no attribute 'mode'`.

## Test Results Summary

| Test | Result |
|------|--------|
| Import SearchRequest from routes.operations | ✓ PASS (exit 0) |
| mode field present in model_fields | ✓ PASS |
| Default value is "text" | ✓ PASS |
| Handler validation code present | ✓ PASS |
| No AttributeError at runtime | ✓ PASS (verified by code inspection) |

## QA Verdict

**PASS** — All acceptance criteria satisfied. The fix is ready for smoke test and closeout.

QA Engineer: gpttalker-tester-qa
Date: 2026-04-10
