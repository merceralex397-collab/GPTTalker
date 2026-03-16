---
name: node-agent-patterns
description: Node agent implementation patterns for GPTTalker. Use when implementing, modifying, or debugging node agent services, hub-to-node communication, local operation execution, health checks, or security boundaries.
---

# Node Agent Patterns — GPTTalker

## What a Node Agent Is

A node agent is a lightweight FastAPI service running on each managed machine in the GPTTalker network. It receives operation requests from the hub over Tailscale and executes them locally — inspecting repos, writing files, forwarding prompts to local LLMs, and reporting results back.

## Hub-to-Node Communication

### Transport

- All hub-to-node traffic flows over **Tailscale** (private WireGuard mesh)
- The hub uses **httpx.AsyncClient** to call node agent HTTP endpoints
- Node agents listen on a known port on their Tailscale IP
- The hub resolves node addresses via the **node registry** (`src/hub/registry/`)

### Request Flow

```
Hub receives MCP tool call from ChatGPT
  → Hub validates inputs (Pydantic)
  → Hub resolves target node via registry
  → Hub sends HTTP request to node agent over Tailscale
  → Node agent executes local operation
  → Node agent returns result
  → Hub assembles MCP response for ChatGPT
```

### Communication Patterns

```python
# Hub-side: calling a node agent
async def call_node_agent(
    client: httpx.AsyncClient,
    node_address: str,
    endpoint: str,
    payload: dict,
    timeout: float = 30.0,
) -> dict:
    url = f"http://{node_address}/{endpoint}"
    response = await client.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()
```

### Timeouts and Retries

- Set explicit timeouts on every hub-to-node request
- Use shorter timeouts for health checks (5s), longer for operations (30-60s)
- Do not retry write operations — they are not idempotent
- Read operations may be retried once on timeout

## Local Operation Execution

### Repo Inspection (`src/node_agent/inspection/`)

| Operation | Endpoint | Description |
|---|---|---|
| Tree | `/inspect/tree` | Walk directory tree up to a given depth |
| File read | `/inspect/file` | Read a file's contents (with size limits) |
| Search | `/inspect/search` | Grep/ripgrep through repo files |
| Git status | `/inspect/git-status` | Get current branch, dirty files, recent commits |

**Rules:**
- All paths are resolved relative to registered repo roots — never accept absolute paths from the hub
- Enforce file size limits on reads (e.g., 1MB max)
- Search results must be truncated if they exceed a response size threshold
- Never follow symlinks outside the repo root

### Markdown Delivery (`src/node_agent/delivery/`)

| Operation | Endpoint | Description |
|---|---|---|
| Write file | `/deliver/write` | Write or overwrite a markdown file |

**Rules:**
- Only write to paths in the **write-target registry** — reject all others
- Validate that the target path is within an allowed repo directory
- Create parent directories if they don't exist
- Use atomic writes (write to temp file, then rename) to avoid partial writes

### Local LLM Communication (`src/node_agent/llm/`)

| Operation | Endpoint | Description |
|---|---|---|
| Forward prompt | `/llm/complete` | Send a prompt to a local LLM service |

**Rules:**
- The node agent forwards prompts to a locally running LLM service (e.g., ollama, llama.cpp server)
- Do not expose the local LLM's raw API — wrap it in a normalized request/response format
- Set timeouts appropriate for LLM inference (may be 60s+)
- Return token usage metadata if available

## Health Check and Capability Advertisement

### Health Endpoint

Every node agent exposes a health endpoint:

```python
@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "node_id": settings.node_id,
        "uptime_seconds": get_uptime(),
        "capabilities": get_capabilities(),
        "repos": list_registered_repos(),
    }
```

### Capability Advertisement

Node agents advertise what they can do:

```python
{
    "capabilities": {
        "inspection": true,      # Can inspect repos
        "delivery": true,        # Can write files
        "llm": true,             # Has a local LLM available
        "search": true,          # Has ripgrep/search installed
        "git": true              # Has git installed
    },
    "repos": [
        {"name": "my-project", "path": "/home/user/my-project", "writable": true},
        {"name": "docs-site", "path": "/home/user/docs-site", "writable": false}
    ]
}
```

The hub uses capability data to route operations correctly and to provide meaningful errors when a node cannot handle a request.

## Security Boundaries

### What Node Agents CAN Do

- Read files within registered repo directories
- Write files to explicitly allowed write targets
- Execute search (grep/ripgrep) within repo directories
- Run `git status` and read git history within repos
- Forward prompts to local LLM services
- Report health and capabilities

### What Node Agents MUST NOT Do

- Execute arbitrary commands or shell scripts
- Access files outside registered repo roots
- Write to paths not in the write-target registry
- Expose the local filesystem beyond registered repos
- Accept requests from sources other than the hub (validate origin)
- Store or cache sensitive data from hub requests
- Modify their own configuration at runtime based on hub requests

### Request Validation

- Every inbound request must include a hub authentication token
- Validate all file paths are within registered repo boundaries (path traversal protection)
- Reject requests for unknown repos or capabilities the node doesn't advertise
- Log all operations with the trace ID provided by the hub
