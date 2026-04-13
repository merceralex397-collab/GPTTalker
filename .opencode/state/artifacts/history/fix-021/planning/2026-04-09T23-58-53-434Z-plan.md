# Plan: FIX-021 — Fix SearchRequest Missing `mode` Field

## Bug Summary

`src/node_agent/routes/operations.py::SearchRequest` (line 39) is missing the `mode` field, but the search handler at line 220 reads `request.mode`. The correct `SearchRequest` model in `src/node_agent/models.py` (line 42) already has `mode: str = Field("text", description="Search mode: text, path, or symbol")`.

## Root Cause

The `SearchRequest` class in `routes/operations.py` (lines 39–46) is missing the `mode` field. The equivalent class in `models.py` (lines 42–52) correctly includes it. The `operations.py` copy was never updated to include `mode`.

## Fix

Add `mode: str = "text"` to `SearchRequest` in `routes/operations.py`, matching the field in `models.py`.

## Changes

### File: `src/node_agent/routes/operations.py`

**Before (lines 39–46):**
```python
class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str
    pattern: str
    include_patterns: list[str] | None = None
    max_results: int = 1000
    timeout: int = 60
```

**After:**
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

## Validation

1. **Syntax/import check**: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.routes.operations import SearchRequest; print(SearchRequest.model_fields.keys())"` exits 0 and shows `mode` in the fields
2. **Full import**: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"` exits 0

## Acceptance Criteria

- [ ] Add `mode` field to `SearchRequest` in `routes/operations.py` matching the model definition in `models.py`
- [ ] `mode` field defaults to `'text'` and accepts `'text'`, `'path'`, and `'symbol'` values
- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.routes.operations import SearchRequest; print(SearchRequest.model_fields.keys())"` exits 0
