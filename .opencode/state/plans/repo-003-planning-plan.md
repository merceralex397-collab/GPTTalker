# REPO-003: search_repo and git_status tools — Implementation Plan

## Overview

Ticket REPO-003 implements two MCP tools for repository inspection:
- **search_repo**: Text search using bounded ripgrep execution
- **git_status**: Read-only git status for approved repositories

Both tools follow the established patterns from REPO-002 (inspect_repo_tree, read_repo_file) and integrate with the existing policy engine, node client, and executor infrastructure.

## 1. Implementation Approach for search_repo Tool

### Strategy
- Use ripgrep (rg) for efficient text search across files
- Execute via bounded subprocess in the node agent's OperationExecutor
- Apply path validation via PathNormalizer before executing search
- Limit search scope to approved repository paths only
- Implement timeout handling at both hub and node-agent levels

### Technical Details
- **ripgrep invocation**: `rg --line-number --no-heading --hidden <pattern> <path>`
- **File filtering**: Support include patterns (e.g., `*.py`, `*.md`)
- **Result limits**: Cap matches at 1000 results per search to prevent large responses
- **Timeout**: 60 seconds for search operations (configurable)

## 2. Implementation Approach for git_status Tool

### Strategy
- Execute git status in read-only mode using `git status --porcelain`
- Execute git branch for current branch name
- Execute git rev-list for ahead/behind count
- Validate repository path via PathNormalizer before execution
- Ensure no git write operations are exposed

### Technical Details
- **git status**: `git -C <path> status --porcelain` for clean/modified/staged/untracked
- **git branch**: `git -C <path> branch --show-current` for current branch
- **git rev-list**: `git -C <path> rev-list --left-right --count HEAD...origin/<branch>` for ahead/behind
- **Timeout**: 30 seconds for git operations

## 3. Hub-Side Handlers

### New File: `src/hub/tools/search.py`

Create handler for search_repo tool:

```python
async def search_repo_handler(
    node_id: str,
    repo_id: str,
    pattern: str,
    path: str = "",
    include_patterns: list[str] | None = None,
    max_results: int = 1000,
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Search for pattern in files within an approved repository.
    
    Validates node, repo, and path before delegating to node agent.
    Returns structured search results with file/line/content information.
    """
```

### New File: `src/hub/tools/git_operations.py`

Create handler for git_status tool:

```python
async def git_status_handler(
    node_id: str,
    repo_id: str,
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Get git status for an approved repository.
    
    Returns branch, clean/dirty status, staged/modified/untracked files,
    and ahead/behind count relative to remote.
    """
```

### Handler Validation Pattern
Both handlers follow the same validation flow:
1. Validate node exists and is accessible
2. Validate repo exists and belongs to node
3. Validate and normalize path (for search)
4. Call node agent via HubNodeClient
5. Format response with MCP-safe structure

## 4. Node-Agent Implementations

### File: `src/node_agent/executor.py` — Add Methods

Add `search_files` method to OperationExecutor:

```python
async def search_files(
    self,
    directory: str,
    pattern: str,
    include_patterns: list[str] | None = None,
    max_results: int = 1000,
    timeout: int = 60,
) -> dict:
    """Search for pattern in files using ripgrep.
    
    Args:
        directory: Directory to search in (must be validated path)
        pattern: Regex pattern to search for
        include_patterns: File patterns to include (e.g., ["*.py"])
        max_results: Maximum number of matches to return
        timeout: Search timeout in seconds
    
    Returns:
        Dict with results, match count, files searched
    """
    # Validate path
    validated_dir = self._validate_path(directory)
    
    # Build ripgrep command
    cmd = ["rg", "--line-number", "--no-heading", "-c"]
    if include_patterns:
        for p in include_patterns:
            cmd.extend(["--glob", p])
    cmd.extend(["--", pattern, str(validated_dir)])
    
    # Execute with subprocess, capture output, parse results
    # Return structured search results
```

Add `git_status` method to OperationExecutor:

```python
async def git_status(
    self,
    repo_path: str,
    timeout: int = 30,
) -> dict:
    """Get git status for a repository.
    
    Args:
        repo_path: Path to git repository (must be validated)
        timeout: Operation timeout in seconds
    
    Returns:
        Dict with branch, status, staged/modified/untracked files, ahead/behind
    """
    # Validate path
    validated_path = self._validate_path(repo_path)
    
    # Check .git exists
    if not (validated_path / ".git").is_dir():
        raise ValueError(f"Not a git repository: {repo_path}")
    
    # Execute git commands:
    # - git status --porcelain
    # - git branch --show-current
    # - git rev-list --left-right --count HEAD...origin/<branch>
    
    # Parse output and return structured status
```

### File: `src/node_agent/routes/operations.py` — Update Endpoints

Update existing stubs to use executor methods:

```python
@router.post("/operations/search", response_model=OperationResponse)
async def search(
    request: SearchRequest,
    executor: OperationExecutor = ExecutorDep,
) -> OperationResponse:
    """Search for pattern in files."""
    try:
        # Validate inputs
        max_results = min(request.max_results, 1000) if request.max_results else 1000
        
        result = await executor.search_files(
            directory=request.directory,
            pattern=request.pattern,
            include_patterns=request.include_patterns,
            max_results=max_results,
            timeout=request.timeout or 60,
        )
        
        return OperationResponse(
            success=True,
            message=f"Found {result['match_count']} matches",
            data=result,
        )
    except PermissionError as e:
        return OperationResponse(success=False, message=str(e))
    except ValueError as e:
        return OperationResponse(success=False, message=str(e))
    except Exception as e:
        return OperationResponse(success=False, message=str(e))


@router.post("/operations/git-status", response_model=OperationResponse)
async def git_status(
    request: GitStatusRequest,
    executor: OperationExecutor = ExecutorDep,
) -> OperationResponse:
    """Get git status for a repository."""
    try:
        result = await executor.git_status(
            repo_path=request.path,
            timeout=request.timeout or 30,
        )
        
        return OperationResponse(
            success=True,
            message="Git status retrieved",
            data=result,
        )
    except PermissionError as e:
        return OperationResponse(success=False, message=str(e))
    except ValueError as e:
        return OperationResponse(success=False, message=str(e))
    except Exception as e:
        return OperationResponse(success=False, message=str(e))
```

### Request Models Update

Update `SearchRequest` and `GitStatusRequest` in `operations.py`:

```python
class SearchRequest(BaseModel):
    """Request to search in files."""
    directory: str
    pattern: str
    include_patterns: list[str] | None = None
    max_results: int = 1000
    timeout: int = 60


class GitStatusRequest(BaseModel):
    """Request to get git status."""
    path: str
    timeout: int = 30
```

## 5. Hub-to-Node Client Methods

### File: `src/hub/services/node_client.py` — Add Methods

Add `search` method (already exists but update to use new endpoint):

```python
async def search(
    self,
    node: NodeInfo,
    directory: str,
    pattern: str,
    include_patterns: list[str] | None = None,
    max_results: int = 1000,
) -> dict[str, Any]:
    """Search for pattern in files on a node.
    
    Args:
        node: Target node information
        directory: Directory to search in
        pattern: Regex pattern to search for
        include_patterns: File patterns to include
        max_results: Maximum matches to return
    
    Returns:
        Search results dictionary
    """
    params = {
        "directory": directory,
        "pattern": pattern,
        "include_patterns": include_patterns,
        "max_results": max_results,
    }
    
    response = await self.post(
        node,
        "/operations/search",
        json=params,
        timeout=60.0,
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("data", {})
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {"success": False, "error": f"Search failed: HTTP {response.status_code}"}
```

Add `git_status` method:

```python
async def git_status(
    self,
    node: NodeInfo,
    repo_path: str,
) -> dict[str, Any]:
    """Get git status for a repository on a node.
    
    Args:
        node: Target node information
        repo_path: Path to the git repository
    
    Returns:
        Git status dictionary
    """
    params = {"path": repo_path}
    
    response = await self.post(
        node,
        "/operations/git-status",
        json=params,
        timeout=30.0,
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("data", {})
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {"success": False, "error": f"Git status failed: HTTP {response.status_code}"}
```

## 6. Policy Integration

### Path Validation
- Use existing `PathNormalizer.validate_no_traversal()` for search path
- Use existing `PathNormalizer.normalize()` to resolve relative paths
- Both hub and node-agent validate paths before operation

### Policy Requirements
Both tools use `READ_REPO_REQUIREMENT` (same as REPO-002):
- requires_node: True
- requires_repo: True

The policy engine validates:
1. Node exists and is healthy
2. Repository is registered and approved
3. Repository belongs to the specified node

### Integration Points
- Hub handlers receive pre-validated node_repo and repo_repo via DI
- Handlers extract repo.path from repo record for path normalization
- Node-agent executor receives validated absolute paths from hub

## 7. Timeout Handling

### Timeouts by Operation
| Operation | Default | Max | Notes |
|-----------|---------|-----|-------|
| search_repo | 60s | 120s | Configurable per-call |
| git_status | 30s | 60s | Typically fast |

### Timeout Propagation
1. Hub client passes timeout to node via request timeout
2. Node agent subprocess uses asyncio.wait_for with timeout
3. Subprocess is killed on timeout to prevent hanging

### Error Handling
- Timeout → Return `{"success": False, "error": "Search timed out after N seconds"}`
- Permission denied → Return `{"success": False, "error": "Permission denied: <path>"}`
- Invalid path → Return `{"success": False, "error": "Path validation failed: <details>"}`
- Git not installed → Return `{"success": False, "error": "Git not available on node"}`
- Not a git repo → Return `{"success": False, "error": "Not a git repository: <path>"}`

## 8. New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/tools/search.py` | Hub-side search_repo handler |
| `src/hub/tools/git_operations.py` | Hub-side git_status handler |

## 9. Existing Files to Modify

| File | Changes |
|------|---------|
| `src/hub/tools/__init__.py` | Add registration for search_repo and git_status tools |
| `src/hub/services/node_client.py` | Add search() and git_status() methods |
| `src/node_agent/executor.py` | Implement search_files() and git_status() methods |
| `src/node_agent/routes/operations.py` | Update search and git-status endpoint stubs |

## 10. Validation Plan

### Unit Tests (src/tests/hub/tools/)
- test_search_repo_handler_validation: Node/repo validation
- test_search_repo_handler_path_validation: Path traversal rejection
- test_git_status_handler_validation: Node/repo validation
- test_git_status_handler_not_git_repo: Error handling

### Integration Tests (src/tests/hub/)
- test_search_repo_integration: Full search flow via mock node
- test_git_status_integration: Full git status flow via mock node

### Node Agent Tests (src/tests/node_agent/)
- test_executor_search_files: Bounded search execution
- test_executor_search_files_timeout: Timeout handling
- test_executor_git_status: Git status parsing
- test_executor_git_status_not_repo: Error handling

### Validation Commands
```bash
# Run linting
ruff check src/hub/tools/search.py src/hub/tools/git_operations.py
ruff check src/node_agent/executor.py
ruff check src/hub/services/node_client.py

# Run tests
pytest src/tests/hub/tools/test_search.py -v
pytest src/tests/hub/tools/test_git_operations.py -v
pytest src/tests/node_agent/test_executor.py -v

# Full validation
make validate
```

## 11. Risk Assessment

### Low Risk
- Pattern follows existing REPO-002 implementation exactly
- Uses existing policy engine and path validation
- Subprocess execution is bounded to validated paths only

### Medium Risk
- ripgrep availability on nodes (assume installed, can add check)
- Git installation verification needed
- Large result sets could impact memory (capped at 1000)

### Mitigations
- Validate ripgrep/git availability at node health check
- Cap results at 1000 matches
- Use subprocess timeout to prevent hanging
- All paths validated before subprocess execution

## 12. Dependencies

- REPO-002:inspect_repo_tree (completed) — establishes pattern
- CORE-004: Hub-to-node client (completed) — provides communication
- CORE-005: Policy engine (completed) — provides path validation
- CORE-006: MCP tool routing (completed) — provides tool registration

## 13. Acceptance Criteria Verification

| Criterion | Verification |
|-----------|--------------|
| Search uses bounded ripgrep execution | subprocess.run with validated path + include patterns |
| Git status is exposed read-only | git status --porcelain (read-only) + no git write commands |
| Timeout handling is explicit | 60s default for search, 30s for git, configurable |

---

**Plan Status**: Ready for review  
**Next Stage**: Implementation (after plan approval)
