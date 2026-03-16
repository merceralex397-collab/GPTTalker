---
name: mcp-protocol
description: MCP protocol implementation guidance for GPTTalker. Use when implementing, modifying, or debugging MCP tool definitions, request/response marshalling, tool registration, or error handling.
---

# MCP Protocol — GPTTalker

## What MCP Is

The Model Context Protocol (MCP) is how ChatGPT invokes tools exposed by GPTTalker. The hub server implements an MCP-compliant tool server that ChatGPT connects to. Each tool has a defined schema, and ChatGPT sends structured requests that the hub validates, routes, executes, and returns.

Reference: https://developers.openai.com/api/docs/mcp/

## Tool Definition Format

Every MCP tool must be defined with a JSON Schema describing its parameters:

```python
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "inspect_repo_tree",
        "description": "List the file tree of a repository on a managed machine.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Registered name of the repository to inspect."
                },
                "depth": {
                    "type": "integer",
                    "description": "Maximum directory depth to traverse.",
                    "default": 3
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Whether to include hidden files and directories.",
                    "default": False
                }
            },
            "required": ["repo_name"]
        }
    }
}
```

### Rules for Tool Definitions

- Every parameter must have a `description`
- Use `required` to mark mandatory parameters
- Provide sensible `default` values for optional parameters
- Tool names use `snake_case`
- Descriptions should be concise but unambiguous — ChatGPT uses them to decide when to call the tool

## Request/Response Marshalling

### Inbound (ChatGPT → Hub)

1. ChatGPT sends a tool call with `name` and `arguments` (JSON string)
2. Hub parses `arguments` into a Pydantic model for validation
3. Hub resolves the target (which node agent, which repo) via registries
4. Hub forwards the operation to the appropriate node agent over Tailscale

```python
from pydantic import BaseModel, Field

class InspectRepoTreeRequest(BaseModel):
    repo_name: str = Field(..., description="Registered repo name")
    depth: int = Field(default=3, ge=1, le=10)
    include_hidden: bool = Field(default=False)
```

### Outbound (Hub → ChatGPT)

Return a JSON-serializable result. MCP tool responses are plain content:

```python
class InspectRepoTreeResponse(BaseModel):
    repo_name: str
    node_id: str
    tree: list[str]
    truncated: bool = False
    error: str | None = None
```

### Marshalling Rules

- Always validate inbound arguments with Pydantic before executing
- Never pass raw JSON strings to tool handlers
- Serialize responses to JSON; strip internal fields (trace IDs, timestamps) from the ChatGPT-facing response
- Large results should be truncated with a `truncated: true` flag

## Tool Registration and Exposure

Tools are registered at hub startup and exposed via the MCP tool listing endpoint:

```python
# src/hub/tools/__init__.py pattern
from src.hub.tools.repo_inspection import REPO_INSPECTION_TOOLS
from src.hub.tools.markdown_delivery import MARKDOWN_DELIVERY_TOOLS
from src.hub.tools.llm_bridge import LLM_BRIDGE_TOOLS
from src.hub.tools.project_context import PROJECT_CONTEXT_TOOLS
from src.hub.tools.cross_repo import CROSS_REPO_TOOLS
from src.hub.tools.routing import ROUTING_TOOLS
from src.hub.tools.observability import OBSERVABILITY_TOOLS

ALL_TOOLS = [
    *REPO_INSPECTION_TOOLS,
    *MARKDOWN_DELIVERY_TOOLS,
    *LLM_BRIDGE_TOOLS,
    *PROJECT_CONTEXT_TOOLS,
    *CROSS_REPO_TOOLS,
    *ROUTING_TOOLS,
    *OBSERVABILITY_TOOLS,
]
```

### Registration Rules

- Each tool module exports a list of tool definitions and a dispatch function
- Tool definitions must match their handler signatures exactly
- New tools must be added to `ALL_TOOLS` and documented in `docs/spec/CANONICAL-BRIEF.md`

## Error Response Format

MCP tool errors should be structured and informative:

```python
class MCPToolError(BaseModel):
    error: str          # Human-readable error message
    error_code: str     # Machine-readable code (e.g., "UNKNOWN_REPO", "NODE_UNREACHABLE")
    tool_name: str      # Which tool failed
    details: dict | None = None  # Optional additional context
```

### Standard Error Codes

| Code | Meaning |
|---|---|
| `UNKNOWN_REPO` | Repo name not found in repo registry |
| `UNKNOWN_NODE` | Node ID not found in node registry |
| `NODE_UNREACHABLE` | Node agent did not respond within timeout |
| `INVALID_TARGET` | Write target not in allowed write-target registry |
| `VALIDATION_ERROR` | Request parameters failed Pydantic validation |
| `EXECUTION_ERROR` | Node agent reported a failure during execution |
| `RATE_LIMITED` | Too many requests to a resource |

### Error Handling Rules

- **Fail closed**: unknown targets → error, never guess or fall back
- Always return the tool name in error responses so ChatGPT knows which call failed
- Log errors with trace IDs via structlog before returning
- Never expose internal stack traces to ChatGPT — return clean error messages
