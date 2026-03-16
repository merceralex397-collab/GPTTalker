# CORE-001: Node registry and management

## Summary

Implement the node registry system that tracks all managed machines in the GPTTalker network. Provide CRUD operations for node registration (name, tailscale_ip, capabilities, status), a list_nodes MCP tool handler for ChatGPT to discover available machines, and a health check mechanism that periodically verifies node agent availability and updates status accordingly.

## Stage

planning

## Status

todo

## Depends On

- SETUP-003
- SETUP-002

## Acceptance Criteria

- [ ] Node model defined with fields: id, name, tailscale_ip, capabilities (JSON), status, last_seen, created_at
- [ ] Register node endpoint creates or updates node record
- [ ] Unregister node endpoint soft-deletes node
- [ ] list_nodes MCP tool returns all active nodes with status
- [ ] Node health check pings node agent health endpoint
- [ ] Status transitions: online → offline after missed health checks
- [ ] Duplicate node name prevention
- [ ] Unit tests for CRUD and health check logic

## Artifacts

- None yet

## Notes

- Capabilities list examples: ["repo_host", "llm_host", "write_target"]
- Health check interval should be configurable (default 60s)
- Consider storing last_error for offline nodes to aid debugging
