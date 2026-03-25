# Backlog Verification — FIX-006

## Ticket
- **ID:** FIX-006
- **Title:** Register read_repo_file tool and close tool surface gaps
- **Stage:** closeout
- **Status:** done
- **Verification state:** PASS

## Verification Summary
The `read_repo_file_handler` was fully implemented in `src/hub/tools/inspection.py` but never registered as a ToolDefinition. The missing registration has been added in `register_inspection_tools()`.

## Evidence
1. **Registration verification:** `read_repo_file` appears in the tool registry with `READ_REPO_REQUIREMENT` policy
2. **Parameter verification:** Handler accepts `node_id`, `repo_id`, `path` parameters matching the schema
3. **Response verification:** File content returned with metadata (encoding, size_bytes, truncated flag)

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| read_repo_file appears in the tool registry | PASS |
| read_repo_file can be called through MCP endpoint | PASS |
| File content is returned with metadata (encoding, size_bytes, truncated) | PASS |

## Notes
- This was a surface gap — the handler existed but wasn't exposed to MCP callers
- No follow-up ticket needed
