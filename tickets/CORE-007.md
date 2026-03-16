# CORE-007: MCP protocol layer

## Summary

Implement the MCP (Model Context Protocol) tool definition and exposure framework that allows ChatGPT to discover and invoke GPTTalker's capabilities. Build a tool registration system, request/response marshalling per the MCP specification, and comprehensive tool call logging with trace IDs. This is the primary interface between ChatGPT and the hub.

## Stage

planning

## Status

todo

## Depends On

- SETUP-002
- SETUP-004

## Acceptance Criteria

- [ ] MCP tool definition framework with name, description, input schema, output schema
- [ ] Tool registration decorator or registry pattern
- [ ] MCP-compliant endpoint for tool discovery (list tools)
- [ ] MCP-compliant endpoint for tool invocation (call tool)
- [ ] Request validation against tool input schemas
- [ ] Response marshalling to MCP format
- [ ] Tool call logging: tool name, input summary, output summary, duration, trace_id
- [ ] Error responses in MCP-compliant format
- [ ] Unit tests for tool registration and invocation

## Artifacts

- None yet

## Notes

- Follow the MCP specification for tool schemas and invocation protocol
- Tool definitions should be co-located with their implementations
- Consider a ToolRegistry singleton that collects all tools at startup
- Log input/output summaries, not full content (can be very large)
