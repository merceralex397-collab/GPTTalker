# Implementation Summary: WRITE-001 - write_markdown with atomic scoped writes

## Overview

Implemented the markdown delivery path with approved write targets, extension allowlists, content hashing, and atomic writes.

## Changes Made

### 1. New File: `src/hub/tools/markdown.py`
- Created hub-side handler `write_markdown_handler`
- Validates node exists and is accessible
- Validates repository is registered and approved
- Validates write target is registered and path is within allowed boundaries
- Validates file extension is in the allowlist for the target
- Validates path doesn't contain traversal attempts
- Calls node agent to perform atomic write with SHA256 verification
- Returns verification metadata including hash

### 2. Modified: `src/hub/services/node_client.py`
- Updated `write_file` method to call `/operations/write-file` endpoint instead of `/files/write`

### 3. Modified: `src/node_agent/executor.py`
- Implemented `write_file` method with:
  - Path validation within allowed boundaries
  - Atomic write using temporary file + os.replace
  - SHA256 hash computation before and after write
  - Verification metadata in response
  - Proper error handling and cleanup

### 4. Modified: `src/node_agent/routes/operations.py`
- Implemented `/operations/write-file` endpoint properly
- Returns verification metadata including path, bytes_written, sha256_hash, verified flag

### 5. Modified: `src/hub/tools/__init__.py`
- Added `WRITE_REQUIREMENT` import
- Created `register_markdown_tools` function
- Registered `write_markdown` tool with `WRITE_REQUIREMENT` policy
- Added markdown tools registration to `register_all_tools`

### 6. Modified: `src/hub/tool_routing/policy_router.py`
- Added `write_target_repo` and `write_target_policy` to type hints
- Added these as optional constructor parameters
- Updated `_execute_handler` to inject these dependencies into handlers

### 7. Modified: `src/hub/dependencies.py`
- Updated `get_policy_aware_router` to include `write_target_repo` and `write_target_policy` dependencies

## Acceptance Criteria Verification

1. **Writes are restricted to approved targets** - ✅
   - WriteTargetPolicy validates path against registered write targets
   - Extension allowlist enforcement
   - Path normalization and traversal prevention

2. **Atomic write behavior is explicit** - ✅
   - Uses temporary file + os.replace for atomicity
   - SHA256 hash computed before write
   - Verification returns hash for client to confirm

3. **Write responses include verification metadata** - ✅
   - Returns `path`, `bytes_written`, `sha256_hash`, `verified`
   - Includes `content_hash_algorithm: "sha256"`

## Files Created/Modified

| File | Change |
|------|--------|
| `src/hub/tools/markdown.py` | Created |
| `src/hub/services/node_client.py` | Modified |
| `src/node_agent/executor.py` | Modified |
| `src/node_agent/routes/operations.py` | Modified |
| `src/hub/tools/__init__.py` | Modified |
| `src/hub/tool_routing/policy_router.py` | Modified |
| `src/hub/dependencies.py` | Modified |

## Validation

- All ruff checks pass
- Code follows existing patterns from similar tools (git_operations.py, inspection.py)
- Proper type hints and docstrings throughout
