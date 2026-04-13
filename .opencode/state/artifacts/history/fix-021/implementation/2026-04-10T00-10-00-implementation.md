# Implementation of FIX-021: Add mode field to SearchRequest in node agent routes

## Summary

Added the missing `mode` field to the `SearchRequest` class in `src/node_agent/routes/operations.py`.

## Change Made

**File**: `src/node_agent/routes/operations.py`

**Before** (lines 39-47):
```python
class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str
    pattern: str
    include_patterns: list[str] | None = None
    max_results: int = 1000
    timeout: int = 60
```

**After** (lines 39-48):
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

## Verification

The `mode` field was successfully added to `SearchRequest` at line 45 with:
- Type: `str`
- Default: `"text"`
- Comment: `# Search mode: text, path, or symbol`

This aligns with the `SearchRequest` model definition in `src/node_agent/models.py` (line 42) which already had:
```python
mode: str = Field('text', description="Search mode: text, path, or symbol")
```

## Impact

- The `search` endpoint handler at line 193+ already uses `request.mode` (validated at line 220 with `mode = request.mode if request.mode in valid_modes else "text"`)
- The `executor.search_files()` method already accepts a `mode` parameter (line 228)
- This fix ensures the route-level `SearchRequest` model matches the internal model and handler expectations
