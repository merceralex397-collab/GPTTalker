# Implementation Plan: FIX-006 - Register read_repo_file tool and close tool surface gaps

## Summary

Add the missing `read_repo_file` tool registration to the MCP tool registry. The handler is already implemented.

## Files Affected

- src/hub/tools/__init__.py - Add ToolDefinition registration

## Implementation Steps

1. Add ToolDefinition registration in register_inspection_tools() function
2. Use READ_REPO_REQUIREMENT policy
3. Register parameters: node_id, repo_id, file_path, offset, limit

## Acceptance Criteria

- [ ] read_repo_file appears in the tool registry
- [ ] read_repo_file can be called through MCP endpoint
- [ ] File content is returned with metadata (encoding, size_bytes, truncated)

## Risk: Low
