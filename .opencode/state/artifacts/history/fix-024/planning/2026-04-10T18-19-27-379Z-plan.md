# FIX-024 Planning — Response Envelope Stripping and Path-Mode Search

## Defect 1: HubNodeClient Response Envelope Stripping

### Root Cause
`HubNodeClient` methods (`read_file`, `search`, `git_status`, `list_directory`) strip the `OperationResponse` envelope by extracting only `data.get("data", {})`. This leaves a payload dict like `{"entries": [...]}` or `{"content": "..."}` with no `success` key.

Hub handlers in `src/hub/tools/inspection.py` and `src/hub/tools/search.py` then call `result.get("success", False)` which always returns `False` for successful operations — making successful node operations appear as failures to MCP callers.

### Affected Methods
- `HubNodeClient.read_file()` — line 208-209
- `HubNodeClient.search()` — line 292-293
- `HubNodeClient.git_status()` — line 324-325
- `HubNodeClient.list_directory()` — line 354-355

### Fix
Change all four methods to return the full `data` (OperationResponse JSON) instead of stripping it. Update hub handlers to extract `result.get("data", {})` for the actual payload.

**node_client.py changes:**
```python
# Before (read_file, search, git_status, list_directory):
return data.get("data", {})

# After:
return data  # full OperationResponse: {"success": True, "data": {...}}
```

**hub handler changes (inspection.py, search.py):**
Extract inner payload from `result.get("data", {})` before using.

### Files to Modify
1. `src/hub/services/node_client.py` — remove envelope stripping
2. `src/hub/tools/inspection.py` — handle full OperationResponse
3. `src/hub/tools/search.py` — handle full OperationResponse

---

## Defect 2: Path-Mode Search Output Parsing

### Root Cause
`executor.py` line 208-210 uses `--files-with-matches` for `mode="path"`:
```python
if mode == "path":
    cmd.extend(["--files-with-matches"])
```
This ripgrep flag outputs just filenames (e.g., `foo.py`) with NO `:` separators.

But lines 254-263 parse output assuming `filename:line_number:content` format:
```python
parts = line.split(":", 2)
if len(parts) >= 2:
    file_path = parts[0]
    try:
        line_num = int(parts[1])  # FAILS for "foo.py" — no colon
```

Since `--files-with-matches` outputs one filename per line (no colons), `parts[1]` raises `ValueError` and path-mode always returns zero matches.

### Fix
Detect path-mode output (mode == "path") before parsing and handle accordingly:
- For `--files-with-matches` output: each non-empty line IS the file path
- No need to split by `:` or extract line numbers

### Files to Modify
1. `src/node_agent/executor.py` — handle path-mode output correctly

---

## Acceptance Criteria
1. HubNodeClient `search/git_status/list_directory/read_file` return full OperationResponse envelopes
2. MCP callers see `success=True` on successful node operations
3. Path-mode search returns file paths with zero match content
4. Existing tests pass or are updated to match production contract
5. `UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.services.node_client import HubNodeClient; from src.node_agent.executor import OperationExecutor; print("OK")' exits 0`
