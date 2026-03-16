---
name: mcp-protocol
description: Hold GPTTalker-specific MCP hub rules for tool contracts, policy enforcement, and fail-closed behavior.
---

# MCP Protocol

Use this skill for hub-side tool planning and implementation.

## Rules

- validate every request against registered nodes, repos, write targets, and service aliases before execution
- keep request and response schemas explicit with Pydantic models
- return structured MCP-safe errors; never leak internal traces
- separate hub policy validation from node execution logic
- keep unrestricted shell access out of the exposed tool surface
