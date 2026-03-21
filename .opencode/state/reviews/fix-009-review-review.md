# Code Review: FIX-009

## Summary
The implementation correctly aligns the `write_markdown` interface with the spec contract.

## Changes Verified

| File | Change | Status |
|------|--------|--------|
| `src/hub/policy/write_target_policy.py` | Added `get(target_id)` method (lines 77-86) | ✅ |
| `src/hub/tools/markdown.py` | Parameter renaming + mode logic + created flag | ✅ |
| `src/hub/tools/__init__.py` | Updated schema with new parameter names | ✅ |
| `src/hub/services/node_client.py` | Added `mode` param to `write_file()` | ✅ |
| `src/node_agent/executor.py` | Mode logic + `created` return | ✅ |
| `src/node_agent/routes/operations.py` | Added `mode` to `WriteFileRequest` | ✅ |

## Acceptance Criteria Verification

1. **Parameter names aligned** ✅
   - `node_id` → `node`
   - `repo_id` → `write_target`  
   - `path` → `relative_path`

2. **Mode parameter** ✅
   - Valid values: `create_or_overwrite` (default), `no_overwrite`
   - Validation at markdown.py:87-88 rejects invalid modes
   - `no_overwrite` raises `FileExistsError` when file exists (executor.py:461-464)

3. **Created flag** ✅
   - Set in executor.py:505 as `created: not file_existed`
   - Propagated through node_client → markdown.py response (line 222)

4. **WriteTargetPolicy.get()** ✅
   - Correctly calls `self._repo.get(target_id)` (line 86)
   - Returns `WriteTargetInfo | None`

5. **No regressions** ✅
   - Atomic write preserved (temp file + os.replace)
   - SHA256 verification preserved

6. **Code quality** ✅
   - Type hints present
   - Error handling in all layers
   - Structured logging with proper context

## Decision: APPROVED

The implementation is correct, complete, and meets all acceptance criteria. No issues found.