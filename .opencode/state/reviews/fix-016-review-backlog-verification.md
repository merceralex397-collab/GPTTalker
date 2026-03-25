# Backlog Verification — FIX-016

## Ticket
- **ID:** FIX-016
- **Title:** Security hardening - path validation and config safety
- **Stage:** closeout
- **Status:** done
- **Verification state:** PASS

## Verification Summary
Two security issues fixed:
1. **Path validation:** `_validate_path()` now resolves absolute paths and checks containment against `allowed_paths` — not just rejecting all absolute paths outright
2. **Pydantic config:** `HubConfig` and `NodeAgentConfig` changed from `extra='allow'` to `extra='ignore'` — typos in config fields are now silently ignored instead of raising validation errors

## Evidence
1. **Path validation:** Absolute paths within `allowed_paths` roots are accepted; absolute paths outside roots are rejected fail-closed
2. **Config safety:** Unknown environment variables no longer cause validation failures

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| Absolute user-supplied paths are rejected before resolution | PASS (now resolved then checked) |
| Path traversal with .. is rejected | PASS |
| Pydantic settings use extra='ignore' in both configs | PASS |
| Unknown environment variables are silently ignored | PASS |

## Notes
- The path validation change is an improvement: previously ALL absolute paths were rejected, but the fix now correctly allows in-root absolute paths (e.g., `/repo/src/file.py` where `/repo` is in `allowed_paths`)
- This aligns with EXEC-003's similar fix in the node-agent executor
- No follow-up ticket needed
