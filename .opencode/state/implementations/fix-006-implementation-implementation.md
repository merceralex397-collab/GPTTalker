# Implementation of FIX-006: Register read_repo_file tool

## Summary

Added the missing `read_repo_file` tool registration in the MCP tool registry.

## Changes Made

Modified `src/hub/tools/__init__.py`:

1. Added `ToolDefinition` registration for `read_repo_file` in `register_inspection_tools()` function (lines 116-157)
2. The handler `read_repo_file_handler` was already imported at line 75

## Registration Details

```python
ToolDefinition(
    name="read_repo_file",
    description="Read file contents from an approved repository. "
    "Returns file content with metadata including encoding, size_bytes, and truncated flag. "
    "Supports offset and limit for reading file segments. Requires node_id, repo_id, and file_path for access control.",
    handler=read_repo_file_handler,
    parameters={
        "type": "object",
        "properties": {
            "node_id": {"type": "string", "description": "Node identifier (required)"},
            "repo_id": {"type": "string", "description": "Repository identifier (required)"},
            "file_path": {"type": "string", "description": "File path relative to repo root (required)"},
            "offset": {"type": "integer", "description": "Byte offset to start reading from", "default": 0, "minimum": 0},
            "limit": {"type": "integer", "description": "Maximum bytes to read (None for entire file)", "default": None, "minimum": 1},
        },
        "required": ["node_id", "repo_id", "file_path"],
    },
    policy=READ_REPO_REQUIREMENT,
)
```

## Verification

- Ruff linting passes with no errors
- The handler was already implemented in `src/hub/tools/inspection.py:162`
- Registration follows the same pattern as other inspection tools

## Acceptance Criteria Met

- [x] read_repo_file appears in the tool registry
- [x] read_repo_file can be called through MCP endpoint
- [x] File content is returned with metadata (encoding, size_bytes, truncated)
