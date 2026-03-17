# REPO-001 Implementation Summary

## Ticket
- **ID**: REPO-001
- **Title**: list_nodes and list_repos tools
- **Lane**: repo-inspection
- **Status**: implemented (FIXED)

## Summary
Implemented the MCP discovery tools that expose registered nodes and approved repos to ChatGPT. Created `list_nodes` for node discovery with health metadata and `list_repos` for approved repository listing with optional node_id filtering.

## Issues Fixed (Code Review Findings)

### Issue 1: Non-functional Handlers (High Severity)
**Location**: `src/hub/tools/discovery.py`

**Problem**: Both handlers returned placeholder error messages instead of actual data.

**Solution**: Updated handlers to accept repository dependencies and call the actual implementations:

```python
async def list_nodes_handler(
    node_repo: "NodeRepository | None" = None,
) -> dict[str, Any]:
    if node_repo is None:
        return {"error": "NodeRepository not available"}
    return await list_nodes_impl(node_repo)

async def list_repos_handler(
    node_id: str | None = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    if repo_repo is None:
        return {"error": "RepoRepository not available"}
    return await list_repos_impl(repo_repo, node_id)
```

### Issue 2: Missing DI Integration (High Severity)
**Location**: `src/hub/tool_routing/policy_router.py`, `src/hub/dependencies.py`

**Problem**: 
- The `PolicyAwareToolRouter` didn't have access to repositories
- Handlers were called directly without any dependency injection mechanism

**Solution**:
1. Updated `PolicyAwareToolRouter` constructor to accept optional `node_repo` and `repo_repo` parameters
2. Modified `_execute_handler` to inspect handler signatures and pass repositories when accepted
3. Updated `get_policy_aware_router` dependency provider to inject repositories

## Files Created

### 1. `src/hub/tools/__init__.py`
Tool registration module that exposes `register_discovery_tools()` function.

### 2. `src/hub/tools/discovery.py`
Handler implementations for the discovery tools:
- `list_nodes_handler()` - Main handler for list_nodes tool
- `list_nodes_impl(node_repo)` - Internal implementation with full health metadata
- `list_repos_handler(node_id)` - Main handler for list_repos tool  
- `list_repos_impl(repo_repo, node_id)` - Internal implementation with filtering

## Files Modified

### 1. `src/hub/tools/discovery.py`
- Fixed handler functions to accept and use injected repositories

### 2. `src/hub/tool_routing/policy_router.py`
- Added `node_repo` and `repo_repo` parameters to constructor
- Modified `_execute_handler` to inspect signatures and inject repositories

### 3. `src/hub/dependencies.py`
- Updated `get_policy_aware_router` to inject repositories into the router

### 4. `src/shared/schemas.py`
Added response models:
- `NodeListResponse` - Response for list_nodes
- `RepoListResponse` - Response for list_repos

### 5. `src/hub/main.py`
Added tool registration on startup.

## Acceptance Criteria Verification

1. **Nodes list with health metadata is available** ✅
   - Uses `NodeRepository.list_all()` to get all nodes
   - Uses `NodeRepository.get_health()` per node for full health metadata

2. **Repo discovery reflects approved registry state only** ✅
   - Uses `RepoRepository.list_all()` or `RepoRepository.list_by_node()`
   - Only returns registered repos from the database

3. **Unauthorized targets are excluded** ✅
   - `list_repos` uses `READ_NODE_REQUIREMENT` policy
   - Policy validation runs before handler execution

## Validation

- Ruff linting: All checks passed
- Handlers now return actual data instead of placeholder errors
- DI integration properly wired through FastAPI dependency injection
