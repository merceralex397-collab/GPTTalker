# REPO-003 Implementation Summary: search_repo and git_status tools

## Overview
Implemented the `search_repo` and `git_status` MCP tools for repository inspection, following the established patterns from REPO-002 (inspect_repo_tree, read_repo_file).

## Files Created

### New Files

1. **src/hub/tools/search.py** - Hub-side handler for search_repo tool
   - Validates node, repo, and path access
   - Uses READ_REPO_REQUIREMENT policy
   - Calls node-agent via HubNodeClient
   - Supports include_patterns (e.g., *.py, *.md)
   - Returns structured results with file/line/content
   - Timeout: configurable up to 120 seconds, default 60s
   - Max results: capped at 1000 matches

2. **src/hub/tools/git_operations.py** - Hub-side handler for git_status tool
   - Validates node and repo access
   - Uses READ_REPO_REQUIREMENT policy
   - Calls node-agent via HubNodeClient
   - Returns branch, is_clean, staged/modified/untracked files
   - Returns ahead/behind count relative to remote
   - Read-only git operations only
   - Timeout: configurable up to 60 seconds, default 30s

## Files Modified

### src/hub/tools/__init__.py
- Added `register_search_tools()` function
- Registers both search_repo and git_status tools with READ_REPO_REQUIREMENT
- Updated `register_all_tools()` to include search tools

### src/hub/services/node_client.py
- Updated `search()` method with new signature using /operations/search endpoint
- Added `git_status()` method using /operations/git-status endpoint
- Removed unused datetime/timezone imports
- Fixed duplicate read_file method (removed duplicate)

### src/node_agent/executor.py
- Implemented `search_files()` method:
  - Uses ripgrep (rg) for efficient text search
  - Validates directory path before execution
  - Supports include_patterns filtering
  - Implements timeout handling with subprocess kill
  - Parses ripgrep output into structured results
  - Returns match count, files searched, and truncated flag
  
- Implemented `git_status()` method:
  - Validates repository path
  - Executes git status --porcelain for file status
  - Executes git branch --show-current for branch name
  - Executes git rev-list for ahead/behind count
  - Returns structured status with staged/modified/untracked
  - All operations are read-only

### src/node_agent/routes/operations.py
- Updated SearchRequest model with max_results and timeout
- Updated GitStatusRequest model with timeout
- Implemented `/operations/search` endpoint using executor
- Implemented `/operations/git-status` endpoint using executor
- Both endpoints include proper error handling and logging

## Acceptance Criteria Verification

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| Search uses bounded ripgrep execution | ✅ | subprocess.run with validated path, include_patterns filtering, timeout handling |
| Git status is exposed read-only | ✅ | Uses git status --porcelain, git branch, git rev-list (all read-only) |
| Timeout and error handling are explicit | ✅ | 60s default for search, 30s for git, configurable up to limits |

## Validation

- All files pass ruff linting
- Imports verified syntactically correct
- Follows established patterns from REPO-002

## Dependencies

- REPO-002: inspect_repo_tree (completed) - established patterns
- CORE-004: Hub-to-node client (completed) - provides communication
- CORE-005: Policy engine (completed) - provides path validation
- CORE-006: MCP tool routing (completed) - provides tool registration
