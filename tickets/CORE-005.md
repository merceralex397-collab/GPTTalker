# CORE-005: Write-target registry

## Summary

Implement the write-target registry that defines approved locations where ChatGPT can write files through the hub. Each write target specifies a node, a root path, and an extension allowlist. This is a critical security boundary — only explicitly registered targets with approved extensions can receive writes.

## Stage

planning

## Status

todo

## Depends On

- CORE-001
- SETUP-003

## Acceptance Criteria

- [ ] WriteTarget model: id, node_id, name (unique), root_path, extension_allowlist (JSON), is_active, created_at
- [ ] Register write target with node ownership validation
- [ ] Extension allowlist enforced (e.g., [".md", ".txt"])
- [ ] Path normalization: resolve symlinks, canonicalize
- [ ] Write target lookup by name
- [ ] List write targets MCP tool
- [ ] Validation: target path must be within declared root
- [ ] Prevent write target overlap (no nested roots on same node)
- [ ] Unit tests for validation and security boundaries

## Artifacts

- None yet

## Notes

- Security first: write targets are the guard rail preventing arbitrary file writes
- Default extension allowlist should be restrictive: [".md", ".txt"]
- Node agent must validate root_path exists and is writable on registration
