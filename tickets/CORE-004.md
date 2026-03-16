# CORE-004: Repo registry and validation

## Summary

Implement the repository registry that tracks all code repositories across the GPTTalker network. Provide CRUD operations for repo registration (node, alias, local_path, metadata), a list_repos MCP tool for ChatGPT to discover available repositories, and robust path validation to prevent directory traversal attacks and ensure repos exist on their declared nodes.

## Stage

planning

## Status

todo

## Depends On

- CORE-001
- SETUP-003

## Acceptance Criteria

- [ ] Repo model: id, node_id, alias (unique), local_path, description, language, is_active, created_at
- [ ] Register repo endpoint with node ownership validation
- [ ] list_repos MCP tool returns repos with node and status info
- [ ] Repo alias uniqueness enforced
- [ ] Path validation: no traversal (../, symlink escape), must be absolute
- [ ] Node agent validates local_path exists on registration
- [ ] Unregister/deactivate repo endpoint
- [ ] Filter repos by node, language, or active status
- [ ] Unit tests for validation and CRUD

## Artifacts

- None yet

## Notes

- Repo alias is the primary identifier used in MCP tool calls (e.g., "gpttalker", "my-api")
- Path validation happens both at registration and at operation time
- Consider caching repo lookups since they're used in every repo operation
