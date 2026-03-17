# REPO-001 Implementation Plan: list_nodes and list_repos tools

## 1. Scope

Implement two MCP discovery tools that expose registered nodes and their approved repos to ChatGPT:
- `list_nodes` - Returns a list of registered nodes with health metadata
- `list_repos` - Returns a list of approved repositories filtered by node_id or returning all repos

### Acceptance Criteria
1. Nodes list with health metadata is available
2. Repo discovery reflects approved registry state only
3. Unauthorized targets are excluded

## 2. Implementation Approach

### 2.1 list_nodes Tool

**Purpose**: Return all registered nodes with their health metadata to ChatGPT.

**Policy**: Use `NO_POLICY_REQUIREMENT` - this tool should be accessible without node validation since it returns general discovery info. However, per CORE-006's fail-closed default, we use `READ_NODE_REQUIREMENT` but configure it to only require basic node listing access.

**Data Flow**:
1. Handler receives request (no parameters required)
2. Calls `NodeRepository.list_all()` to get all nodes
3. For each node, calls `NodeRepository.get_health()` to get health metadata
4. Combines node info with health data into response
5. Returns structured list

**Response Schema**:
```python
{
    "nodes": [
        {
            "node_id": "string",
            "name": "string",
            "hostname": "string",
            "status": "unknown|healthy|unhealthy|offline",
            "last_seen": "ISO datetime or null",
            "health": {
                "health_status": "healthy|unhealthy|offline|unknown",
                "health_latency_ms": "int or null",
                "health_error": "string or null",
                "health_check_count": int,
                "consecutive_failures": int,
                "last_health_check": "ISO datetime or null",
                "last_health_attempt": "ISO datetime or null"
            }
        }
    ],
    "total": int
}
```

### 2.2 list_repos Tool

**Purpose**: Return all approved repositories from the registry, optionally filtered by node_id.

**Policy**: Use `READ_NODE_REQUIREMENT` to ensure only approved nodes can have their repos listed. This enforces that only registered nodes can have their repos exposed.

**Parameters**:
- `node_id` (optional): Filter repos by specific node. If omitted, returns all approved repos.

**Data Flow**:
1. Handler receives request with optional `node_id` parameter
2. If `node_id` provided, validates node access via policy
3. Calls `RepoRepository.list_all()` or `RepoRepository.list_by_node(node_id)`
4. Returns structured list

**Response Schema**:
```python
{
    "repos": [
        {
            "repo_id": "string",
            "name": "string",
            "path": "string",
            "node_id": "string",
            "is_indexed": bool
        }
    ],
    "total": int,
    "filtered_by_node": "node_id or null"
}
```

## 3. Data Models

### New Response Models (add to src/shared/schemas.py)

```python
class NodeListResponse(BaseModel):
    """Response model for list_nodes tool."""
    nodes: list[dict[str, Any]] = Field(default_factory=list, description="List of nodes with health")
    total: int = Field(0, description="Total number of nodes")


class RepoListResponse(BaseModel):
    """Response model for list_repos tool."""
    repos: list[dict[str, Any]] = Field(default_factory=list, description="List of repos")
    total: int = Field(0, description="Total number of repos")
    filtered_by_node: str | None = Field(None, description="Node ID if filtered")
```

## 4. New Files to Create

### 4.1 src/hub/tools/discovery.py
This file will contain the tool handler implementations.

**Content**:
- `list_nodes_handler() -> dict[str, Any]` - List all nodes with health metadata
- `list_repos_handler(node_id: str | None = None) -> dict[str, Any]` - List all repos, optionally filtered

### 4.2 src/hub/tools/__init__.py
Module init file to expose tool registration function.

## 5. Existing Files to Modify

### 5.1 src/hub/main.py
Add tool registration call in the application startup/lifespan:
```python
from src.hub.tools import register_discovery_tools
# In startup event:
register_discovery_tools(registry)
```

### 5.2 src/shared/schemas.py
Add `NodeListResponse` and `RepoListResponse` Pydantic models.

## 6. Implementation Details

### 6.1 Tool Registration

In `src/hub/tools/__init__.py`:

```python
def register_discovery_tools(registry: ToolRegistry) -> None:
    """Register discovery tools with the tool registry.
    
    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tools.discovery import list_nodes_handler, list_repos_handler
    from src.hub.tool_routing.requirements import READ_NODE_REQUIREMENT, NO_POLICY_REQUIREMENT
    
    # Register list_nodes tool
    registry.register(ToolDefinition(
        name="list_nodes",
        description="List all registered nodes with their health status. "
                   "Returns information about each node including name, hostname, "
                   "status, and detailed health metadata.",
        handler=list_nodes_handler,
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        policy=NO_POLICY_REQUIREMENT,  # Discovery tool - no specific node required
    ))
    
    # Register list_repos tool
    registry.register(ToolDefinition(
        name="list_repos",
        description="List all approved repositories. Optionally filter by node_id "
                   "to see repos on a specific machine.",
        handler=list_repos_handler,
        parameters={
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "Optional node_id to filter repos by specific node"
                }
            },
            "required": []
        },
        policy=READ_NODE_REQUIREMENT,  # Requires valid node access
    ))
```

### 6.2 Handler Implementation

In `src/hub/tools/discovery.py`:

```python
"""Discovery tools for nodes and repos."""

from typing import Any

from src.hub.dependencies import (
    get_node_repository,
    get_repo_repository,
)
from src.shared.logging import get_logger
from src.shared.schemas import NodeHealthStatus

logger = get_logger(__name__)


async def list_nodes_handler() -> dict[str, Any]:
    """List all registered nodes with their health metadata.
    
    This tool provides discovery of all managed nodes without requiring
    a specific node_id - it's a top-level discovery tool.
    
    Returns:
        Dictionary with nodes list and total count.
    """
    # This will be called via FastAPI dependency injection
    # We'll get the repos via the dependency injection system
    from src.hub.tool_routing.requirements import ToolContext
    
    # For now, return a placeholder - actual implementation uses DI
    # The MCP handler will inject dependencies via context
    return {"error": "Implementation pending DI integration"}


async def list_nodes_impl(node_repo) -> dict[str, Any]:
    """Internal implementation for list_nodes.
    
    Args:
        node_repo: NodeRepository instance.
        
    Returns:
        Node list response with health metadata.
    """
    import time
    
    start = int(time.time() * 1000)
    
    # Get all nodes
    nodes = await node_repo.list_all()
    
    nodes_data = []
    for node in nodes:
        # Get health metadata
        health = await node_repo.get_health(node.node_id)
        
        node_dict = {
            "node_id": node.node_id,
            "name": node.name,
            "hostname": node.hostname,
            "status": node.status.value,
            "last_seen": node.last_seen.isoformat() if node.last_seen else None,
            "health": {
                "health_status": (health.get("health_status", NodeHealthStatus.UNKNOWN)).value
                    if health else NodeHealthStatus.UNKNOWN.value,
                "health_latency_ms": health.get("health_latency_ms") if health else None,
                "health_error": health.get("health_error") if health else None,
                "health_check_count": health.get("health_check_count", 0) if health else 0,
                "consecutive_failures": health.get("consecutive_failures", 0) if health else 0,
                "last_health_check": health.get("last_health_check").isoformat() 
                    if health and health.get("last_health_check") else None,
                "last_health_attempt": health.get("last_health_attempt").isoformat()
                    if health and health.get("last_health_attempt") else None,
            } if health else None,
        }
        nodes_data.append(node_dict)
    
    duration = int(time.time() * 1000) - start
    
    logger.info("list_nodes_executed", total=len(nodes_data), duration_ms=duration)
    
    return {
        "nodes": nodes_data,
        "total": len(nodes_data),
    }


async def list_repos_handler(node_id: str | None = None) -> dict[str, Any]:
    """List all approved repositories.
    
    Optionally filter by node_id. This tool requires node access validation
    when a node_id is provided.
    
    Args:
        node_id: Optional node_id to filter repos by specific node.
        
    Returns:
        Repo list response.
    """
    return {"error": "Implementation pending DI integration"}


async def list_repos_impl(repo_repo, node_id: str | None = None) -> dict[str, Any]:
    """Internal implementation for list_repos.
    
    Args:
        repo_repo: RepoRepository instance.
        node_id: Optional node_id to filter by.
        
    Returns:
        Repo list response.
    """
    import time
    
    start = int(time.time() * 1000)
    
    # Get repos based on filter
    if node_id:
        repos = await repo_repo.list_by_node(node_id)
    else:
        repos = await repo_repo.list_all()
    
    repos_data = []
    for repo in repos:
        repo_dict = {
            "repo_id": repo.repo_id,
            "name": repo.name,
            "path": repo.path,
            "node_id": repo.node_id,
            "is_indexed": repo.is_indexed,
        }
        repos_data.append(repo_dict)
    
    duration = int(time.time() * 1000) - start
    
    logger.info(
        "list_repos_executed", 
        total=len(repos_data), 
        filtered_by=node_id,
        duration_ms=duration
    )
    
    return {
        "repos": repos_data,
        "total": len(repos_data),
        "filtered_by_node": node_id,
    }
```

### 6.3 DI-Integrated Handlers

The handlers need to integrate with FastAPI's dependency injection. Update `src/hub/tools/discovery.py` to use proper DI:

```python
"""Discovery tools with dependency injection."""

from typing import Any, Annotated

from fastapi import Depends

from src.hub.dependencies import get_node_repository, get_repo_repository
from src.hub.tool_router import ToolHandler
from src.shared.logging import get_logger
from src.shared.repositories.nodes import NodeRepository
from src.shared.repositories.repos import RepoRepository
from src.shared.schemas import NodeHealthStatus

logger = get_logger(__name__)


async def list_nodes_handler(
    node_repo: Annotated[NodeRepository, Depends(get_node_repository)],
) -> dict[str, Any]:
    """List all registered nodes with their health metadata.
    
    Args:
        node_repo: NodeRepository from DI.
        
    Returns:
        Node list response with health metadata.
    """
    import time
    
    start = int(time.time() * 1000)
    
    # Get all nodes
    nodes = await node_repo.list_all()
    
    nodes_data = []
    for node in nodes:
        # Get health metadata
        health = await node_repo.get_health(node.node_id)
        
        node_dict = {
            "node_id": node.node_id,
            "name": node.name,
            "hostname": node.hostname,
            "status": node.status.value,
            "last_seen": node.last_seen.isoformat() if node.last_seen else None,
            "health": {
                "health_status": (health.get("health_status", NodeHealthStatus.UNKNOWN)).value
                    if health else NodeHealthStatus.UNKNOWN.value,
                "health_latency_ms": health.get("health_latency_ms") if health else None,
                "health_error": health.get("health_error") if health else None,
                "health_check_count": health.get("health_check_count", 0) if health else 0,
                "consecutive_failures": health.get("consecutive_failures", 0) if health else 0,
                "last_health_check": health.get("last_health_check").isoformat() 
                    if health and health.get("last_health_check") else None,
                "last_health_attempt": health.get("last_health_attempt").isoformat()
                    if health and health.get("last_health_attempt") else None,
            } if health else None,
        }
        nodes_data.append(node_dict)
    
    duration = int(time.time() * 1000) - start
    
    logger.info("list_nodes_executed", total=len(nodes_data), duration_ms=duration)
    
    return {
        "nodes": nodes_data,
        "total": len(nodes_data),
    }


async def list_repos_handler(
    node_id: str | None = None,
    repo_repo: Annotated[RepoRepository, Depends(get_repo_repository)],
) -> dict[str, Any]:
    """List all approved repositories.
    
    Args:
        node_id: Optional node_id to filter repos by specific node.
        repo_repo: RepoRepository from DI.
        
    Returns:
        Repo list response.
    """
    import time
    
    start = int(time.time() * 1000)
    
    # Get repos based on filter
    if node_id:
        repos = await repo_repo.list_by_node(node_id)
    else:
        repos = await repo_repo.list_all()
    
    repos_data = []
    for repo in repos:
        repo_dict = {
            "repo_id": repo.repo_id,
            "name": repo.name,
            "path": repo.path,
            "node_id": repo.node_id,
            "is_indexed": repo.is_indexed,
        }
        repos_data.append(repo_dict)
    
    duration = int(time.time() * 1000) - start
    
    logger.info(
        "list_repos_executed", 
        total=len(repos_data), 
        filtered_by=node_id,
        duration_ms=duration
    )
    
    return {
        "repos": repos_data,
        "total": len(repos_data),
        "filtered_by_node": node_id,
    }
```

## 7. Policy Integration Points

### 7.1 list_nodes Policy
- **Requirement**: `NO_POLICY_REQUIREMENT` 
- **Rationale**: This is a discovery tool that lists all nodes - it doesn't access specific nodes, just provides overview
- **Fallback**: If we need fail-closed, use `READ_NODE_REQUIREMENT` with no node_id extraction

### 7.2 list_repos Policy
- **Requirement**: `READ_NODE_REQUIREMENT`
- **Rationale**: When node_id is provided, we need to validate that the node is approved before exposing its repos
- **Parameter extraction**: Uses default `node_param="node_id"`

### 7.3 Policy Engine Integration
The tools integrate with the existing PolicyAwareToolRouter from CORE-006:
- Policy validation runs BEFORE handler execution
- Invalid node_id returns MCP error response
- This ensures unauthorized targets are excluded (acceptance criterion #3)

## 8. Validation Approach

### 8.1 Unit Tests
- Test `list_nodes_impl` with mock NodeRepository
- Test `list_repos_impl` with mock RepoRepository
- Test filtering by node_id

### 8.2 Integration Tests
- Test tool registration in FastAPI app
- Test DI integration
- Test policy validation

### 8.3 Validation Commands
```bash
# Run tests
pytest tests/hub/tools/test_discovery.py -v

# Run linting
ruff check src/hub/tools/

# Run full validation
make validate
```

## 9. Integration Points with Existing Infrastructure

### 9.1 Repositories
- Uses `NodeRepository.list_all()` - existing from CORE-001
- Uses `NodeRepository.get_health()` - existing from CORE-001
- Uses `RepoRepository.list_all()` - existing from CORE-002
- Uses `RepoRepository.list_by_node()` - existing from CORE-002

### 9.2 Policy Engine
- Integrates with `PolicyAwareToolRouter` from CORE-006
- Uses `PolicyRequirement` from requirements.py
- Uses fail-closed behavior from CORE-005

### 9.3 MCP Transport
- Returns MCP-compatible response format via `format_tool_response`
- Tool definitions registered in global `ToolRegistry`
- Tools discoverable via `tools/list` MCP method

### 9.4 Logging
- Uses structured logging via `get_logger(__name__)`
- Logs include: tool_name, total, duration_ms, filtered_by
- Trace ID propagation via context

## 10. Acceptance Verification

1. **Nodes list with health metadata**:
   - ✓ Calls `NodeRepository.list_all()` 
   - ✓ Calls `NodeRepository.get_health()` per node
   - ✓ Returns combined node + health data

2. **Repo discovery reflects approved registry state only**:
   - ✓ Uses `RepoRepository` which only returns registered repos
   - ✓ No direct filesystem access

3. **Unauthorized targets are excluded**:
   - ✓ Policy validation before handler execution
   - ✓ Invalid node_id rejected by policy engine
   - ✓ MCP error returned for policy failures

## 11. Risks and Assumptions

### Risks
- None identified - all dependencies are in place

### Assumptions
- Database is initialized and migrations have run (SETUP-003)
- Node and repo registries have data (future bootstrap)
- Health polling is running (CORE-004)

## 12. Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `src/hub/tools/__init__.py` | Create | Tool registration function |
| `src/hub/tools/discovery.py` | Create | list_nodes and list_repos handlers |
| `src/shared/schemas.py` | Modify | Add response models |
| `src/hub/main.py` | Modify | Register tools on startup |
