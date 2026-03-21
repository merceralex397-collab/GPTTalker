# Implementation of FIX-007: Fix ripgrep search parser and implement search modes

## Summary

Fixed two search defects:
1. **Ripgrep -c flag bug**: Removed `-c` flag and fixed the parser to correctly extract file path, line number, and match content
2. **Search mode parameter**: Added mode parameter with text/path/symbol options

## Changes Made

### 1. src/node_agent/executor.py
- Removed `-c` (count) flag from ripgrep command
- Fixed parser to use `split(":", 2)` instead of `split(":", 3)` since content no longer has count
- Added `mode` parameter to `search_files()` method with three options:
  - `text` (default): Normal content search
  - `path`: Uses `--files-with-matches` to search file paths
  - `symbol`: Uses `--word-regexp` for whole-word identifier search
- Added mode to return dictionary for response consistency

### 2. src/hub/tools/search.py
- Added `mode` parameter to `search_repo_handler()` with default "text"
- Added mode validation against allowed values ["text", "path", "symbol"]
- Passes mode to `node_client.search()`
- Returns mode in response dictionary

### 3. src/hub/services/node_client.py
- Added `mode` parameter to `search()` method with default "text"
- Passes mode in the request params to node agent

### 4. src/node_agent/models.py
- Added `mode` field to `SearchRequest` with default "text"
- Added `max_results` and `timeout` fields to the request model

### 5. src/node_agent/routes/operations.py
- Added mode validation in search endpoint
- Passes mode to executor's search_files method
- Added mode to log output

### 6. src/hub/tools/__init__.py
- Added `mode` parameter to search_repo tool schema with enum ["text", "path", "symbol"]

## Validation

- Ripgrep now returns content lines instead of counts
- Parser correctly extracts file path, line number, and content
- Search mode is validated and defaults to "text" for invalid values
- All tool chain components (handler → client → routes → executor) now support mode parameter
