# Plan: FIX-007 - Fix ripgrep search parser and implement search modes

## Issues
1. Ripgrep -c flag causes parser mismatch
2. search_repo lacks mode parameter

## Fix

### Issue 1: Ripgrep Parser
- Remove `-c` flag from ripgrep command (line 187 in executor.py)
- Change parser to handle format: `filename:line_number:line_content`
- Parser should split on `:` with max 2 splits

### Issue 2: Mode Parameter
- `text`: Default regex search (current behavior)
- `path`: Search in file paths using `--search-zip` and file filtering
- `symbol`: Use `-w` flag for word-boundary matching (class/function definitions)

## Files
- src/node_agent/executor.py: Fix ripgrep command and parser
- src/hub/tools/search.py: Add mode parameter
- src/hub/services/node_client.py: Add mode parameter  
- src/hub/tools/__init__.py: Add mode to schema

## Acceptance
- [ ] Search returns non-zero matches
- [ ] Parser extracts file, line, content
- [ ] mode parameter with text/path/symbol works
