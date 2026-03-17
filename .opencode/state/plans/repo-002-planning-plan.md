# REPO-002 Implementation Plan: inspect_repo_tree and read_repo_file Tools

## 1. Implementation Overview

This ticket implements two MCP tools for repository inspection:
- `inspect_repo_tree`: Lists directory contents within approved repos
- `read_repo_file`: Reads file contents with offset/limit support

### Architecture Pattern

```
ChatGPT → Hub (policy validation) → Node Agent (bounded file ops)
         ├── validate node_id (NodePolicy)
         ├── validate repo_id (RepoPolicy)
         ├── normalize & validate path (PathNormalizer)
         └── proxy to node-agent via HubNodeClient
```

## 2. inspect_repo_tree Tool Implementation

### 2.1 Hub-Side Handler

**File**: `src/hub/tools/inspection.py` (NEW)

```python
async def inspect_repo_tree_handler(
    node_id: str,
    repo_id: str,
    path: str = "",
    max_entries: int = 100,
    node_client: HubNodeClient | None = None,
    node_repo: NodeRepository | None = None,
    repo_repo: RepoRepository | None = None,
) -> dict[str, Any]:
    """List directory contents within an approved repository.
    
    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier to inspect.
        path: Directory path relative to repo root (default: root).
        max_entries: Maximum entries to return (default: 100).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        repo_repo: RepoRepository for repo lookup.
    
    Returns:
        Dict with repo tree entries and metadata.
    """
```

**Policy Requirements**: `READ_REPO_REQUIREMENT` (requires node + repo validation)

**Flow**:
1. Validate node_id via NodePolicy (CORE-005)
2. Validate repo_id via RepoPolicy (CORE-005)
3. Get repo info (path) from RepoRepository
4. Normalize relative path against repo.path using PathNormalizer
5. Call node-agent `/operations/list-dir` endpoint
6. Transform node response to MCP format

### 2.2 MCP Request Schema

```json
{
  "type": "object",
  "properties": {
    "node_id": {
      "type": "string",
      "description": "Node identifier (required)"
    },
    "repo_id": {
      "type": "string", 
      "description": "Repository identifier (required)"
    },
    "path": {
      "type": "string",
      "description": "Directory path relative to repo root (default: root)",
      "default": ""
    },
    "max_entries": {
      "type": "integer",
      "description": "Maximum entries to return",
      "default": 100,
      "maximum": 500
    }
  },
  "required": ["node_id", "repo_id"]
}
```

### 2.3 MCP Response Schema

```python
{
  "repo_id": str,
  "node_id": str,
  "path": str,
  "entries": [
    {
      "name": str,
      "path": str, 
      "is_dir": bool,
      "size": int | None,
      "modified": datetime | None
    }
  ],
  "total_count": int,
  "truncated": bool
}
```

## 3. read_repo_file Tool Implementation

### 3.1 Hub-Side Handler

**File**: `src/hub/tools/inspection.py` (SAME FILE, NEW FUNCTION)

```python
async def read_repo_file_handler(
    node_id: str,
    repo_id: str,
    file_path: str,
    offset: int = 0,
    limit: int | None = None,
    node_client: HubNodeClient | None = None,
    node_repo: NodeRepository | None = None,
    repo_repo: RepoRepository | None = None,
) -> dict[str, Any]:
    """Read file contents from an approved repository.
    
    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier.
        file_path: File path relative to repo root.
        offset: Byte offset to start reading from (default: 0).
        limit: Maximum bytes to read (None for entire file).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        repo_repo: RepoRepository for repo lookup.
    
    Returns:
        Dict with file content and metadata.
    """
```

**Policy Requirements**: `READ_REPO_REQUIREMENT` (requires node + repo validation)

**Flow**:
1. Validate node_id via NodePolicy
2. Validate repo_id via RepoPolicy
3. Get repo info from RepoRepository
4. Normalize file path against repo.path using PathNormalizer
5. Validate path doesn't escape repo (PathNormalizer.validate_symlinks)
6. Call node-agent `/operations/read-file` endpoint
7. Transform node response to MCP format

### 3.2 MCP Request Schema

```json
{
  "type": "object",
  "properties": {
    "node_id": {
      "type": "string",
      "description": "Node identifier (required)"
    },
    "repo_id": {
      "type": "string",
      "description": "Repository identifier (required)"
    },
    "file_path": {
      "type": "string",
      "description": "File path relative to repo root (required)"
    },
    "offset": {
      "type": "integer",
      "description": "Byte offset to start reading from",
      "default": 0,
      "minimum": 0
    },
    "limit": {
      "type": "integer",
      "description": "Maximum bytes to read (None for entire file)",
      "default": null,
      "minimum": 1
    }
  },
  "required": ["node_id", "repo_id", "file_path"]
}
```

### 3.3 MCP Response Schema

```python
{
  "repo_id": str,
  "node_id": str,
  "file_path": str,
  "content": str,
  "encoding": str,  # "utf-8"
  "size_bytes": int,
  "truncated": bool,
  "offset": int,
  "bytes_read": int
}
```

## 4. Node-Agent Implementation

### 4.1 Update OperationExecutor

**File**: `src/node_agent/executor.py`

Implement the bounded file operations:

```python
async def list_directory(self, path: str, max_entries: int = 100) -> list[dict]:
    """List directory contents with metadata."""
    self._validate_path(path)
    
    base_path = Path(path)
    if not base_path.is_dir():
        raise ValueError(f"Not a directory: {path}")
    
    entries = []
    for entry in base_path.iterdir():
        stat = entry.stat()
        entries.append({
            "name": entry.name,
            "path": str(entry),
            "is_dir": entry.is_dir(),
            "size": stat.st_size if entry.is_file() else None,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        })
        
        if len(entries) >= max_entries:
            break
    
    return entries


async def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> dict:
    """Read file with offset and limit support."""
    self._validate_path(path)
    
    file_path = Path(path)
    if not file_path.is_file():
        raise ValueError(f"Not a file: {path}")
    
    # Get file size
    file_size = file_path.stat().st_size
    
    # Read with offset/limit
    with open(file_path, 'rb') as f:
        f.seek(offset)
        
        if limit:
            content = f.read(limit)
        else:
            content = f.read()
    
    content_str = content.decode('utf-8')
    
    return {
        "content": content_str,
        "size_bytes": file_size,
        "bytes_read": len(content),
        "offset": offset,
        "truncated": (offset + len(content)) < file_size
    }
```

### 4.2 Update Operations Routes

**File**: `src/node_agent/routes/operations.py`

Implement the actual endpoints:

```python
from src.node_agent.dependencies import ExecutorDep
from src.shared.logging import get_logger

logger = get_logger(__name__)

@router.post("/operations/list-dir", response_model=OperationResponse)
async def list_dir(
    request: ListDirRequest,
    executor: OperationExecutor = ExecutorDep,
) -> OperationResponse:
    """List directory contents."""
    try:
        entries = await executor.list_directory(request.path, request.max_entries)
        
        return OperationResponse(
            success=True,
            message=f"Listed {len(entries)} entries",
            data={
                "entries": entries,
                "total": len(entries),
                "path": request.path,
            }
        )
    except PermissionError as e:
        logger.warning("list_dir_permission_denied", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("list_dir_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )


@router.post("/operations/read-file", response_model=OperationResponse)
async def read_file(
    request: ReadFileRequest,
    executor: OperationExecutor = ExecutorDep,
) -> OperationResponse:
    """Read file contents."""
    try:
        result = await executor.read_file(request.path, request.offset, request.limit)
        
        return OperationResponse(
            success=True,
            message=f"Read {result['bytes_read']} bytes",
            data=result,
        )
    except PermissionError as e:
        logger.warning("read_file_permission_denied", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except ValueError as e:
        logger.warning("read_file_invalid_path", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("read_file_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
```

### 4.3 Update Request Models

**File**: `src/node_agent/routes/operations.py`

Add new fields to request models:

```python
class ListDirRequest(OperationRequest):
    """Request to list directory contents."""
    
    max_entries: int = 100


class ReadFileRequest(OperationRequest):
    """Request to read a file."""
    
    offset: int = 0
    limit: int | None = None
```

## 5. Hub-to-Node Communication

### 5.1 Add Methods to HubNodeClient

**File**: `src/hub/services/node_client.py`

```python
async def list_directory(
    self,
    node: NodeInfo,
    path: str,
    max_entries: int = 100,
) -> dict[str, Any]:
    """List directory on a node.
    
    Args:
        node: Target node.
        path: Directory path to list.
        max_entries: Maximum entries to return.
    
    Returns:
        Directory listing or error.
    """
    params = {
        "path": path,
        "max_entries": max_entries,
    }
    
    response = await self.get(node, "/operations/list-dir", params=params, timeout=30.0)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("data", {})
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {
        "success": False,
        "error": f"Failed to list directory: HTTP {response.status_code}",
    }


async def read_file(
    self,
    node: NodeInfo,
    path: str,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    """Read file from a node.
    
    Args:
        node: Target node.
        path: File path to read.
        offset: Byte offset.
        limit: Maximum bytes to read.
    
    Returns:
        File content or error.
    """
    params = {"path": path, "offset": offset}
    if limit is not None:
        params["limit"] = limit
    
    response = await self.get(node, "/operations/read-file", params=params, timeout=30.0)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("data", {})
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {
        "success": False,
        "error": f"Failed to read file: HTTP {response.status_code}",
    }
```

## 6. Policy Integration

### 6.1 Path Validation in Hub Handlers

The hub validates paths before sending to node-agent:

```python
from src.hub.policy.path_utils import PathNormalizer, PathValidationResult
from src.shared.exceptions import PathTraversalError

# Inside handler:
try:
    # Get repo base path
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        return {"success": False, "error": f"Repository not found: {repo_id}"}
    
    # Normalize and validate path
    if path:  # For inspect_repo_tree
        normalized = PathNormalizer.normalize(path, repo.path)
        PathNormalizer.validate_symlinks(normalized, repo.path)
    else:  # For read_repo_file
        normalized = PathNormalizer.normalize(file_path, repo.path)
        PathNormalizer.validate_symlinks(normalized, repo.path)
        
except PathTraversalError as e:
    return {"success": False, "error": f"Path validation failed: {e}"}
```

### 6.2 Policy Requirement Definition

**File**: `src/hub/tools/inspection.py`

Define custom policy requirement for repo inspection:

```python
from src.hub.tool_routing.requirements import PolicyRequirement
from src.hub.policy.scopes import OperationScope

# Custom requirement for repo inspection tools
INSPECT_REPO_REQUIREMENT = PolicyRequirement(
    scope=OperationScope.READ,
    requires_node=True,
    requires_repo=True,
    node_param="node_id",
    repo_param="repo_id",
)
```

## 7. Tool Registration

### 7.1 Register Tools

**File**: `src/hub/tools/__init__.py` (MODIFY)

Add import and registration:

```python
from src.hub.tools.inspection import (
    inspect_repo_tree_handler,
    read_repo_file_handler,
    INSPECT_REPO_REQUIREMENT,
)


def register_inspection_tools(registry: ToolRegistry) -> None:
    """Register inspection tools."""
    from src.hub.tool_router import ToolDefinition
    
    # inspect_repo_tree
    registry.register(
        ToolDefinition(
            name="inspect_repo_tree",
            description="List directory contents within an approved repository. "
            "Returns file and directory entries with metadata. "
            "Requires node_id and repo_id for access control.",
            handler=inspect_repo_tree_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Node identifier"},
                    "repo_id": {"type": "string", "description": "Repository identifier"},
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to repo root",
                        "default": "",
                    },
                    "max_entries": {
                        "type": "integer",
                        "description": "Maximum entries to return",
                        "default": 100,
                        "maximum": 500,
                    },
                },
                "required": ["node_id", "repo_id"],
            },
            policy=INSPECT_REPO_REQUIREMENT,
        )
    )
    
    # read_repo_file
    registry.register(
        ToolDefinition(
            name="read_repo_file",
            description="Read file contents from an approved repository. "
            "Supports offset and limit for partial reads. "
            "Requires node_id and repo_id for access control.",
            handler=read_repo_file_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string", "description": "Node identifier"},
                    "repo_id": {"type": "string", "description": "Repository identifier"},
                    "file_path": {
                        "type": "string",
                        "description": "File path relative to repo root",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Byte offset to start reading from",
                        "default": 0,
                        "minimum": 0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum bytes to read",
                        "default": None,
                        "minimum": 1,
                    },
                },
                "required": ["node_id", "repo_id", "file_path"],
            },
            policy=INSPECT_REPO_REQUIREMENT,
        )
    )
```

### 7.2 Update Hub Startup

**File**: `src/hub/tools/__init__.py`

Update tool registration in main startup:

```python
def register_all_tools(registry: ToolRegistry) -> None:
    """Register all hub tools."""
    from src.hub.tools.discovery import register_discovery_tools
    from src.hub.tools.inspection import register_inspection_tools
    
    register_discovery_tools(registry)
    register_inspection_tools(registry)
```

## 8. New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/tools/inspection.py` | Hub-side handlers for inspect_repo_tree and read_repo_file |

## 9. Existing Files to Modify

| File | Changes |
|------|---------|
| `src/hub/services/node_client.py` | Add `list_directory()` and `read_file()` methods |
| `src/hub/tools/__init__.py` | Add inspection tool registration |
| `src/node_agent/executor.py` | Implement `list_directory()` and `read_file()` |
| `src/node_agent/routes/operations.py` | Implement list-dir and read-file endpoints |

## 10. Validation Plan

### 10.1 Unit Tests (Hub Handlers)

```python
# tests/hub/tools/test_inspection.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.hub.tools.inspection import (
    inspect_repo_tree_handler,
    read_repo_file_handler,
)


class TestInspectRepoTree:
    """Tests for inspect_repo_tree handler."""
    
    async def test_success(self):
        """Test successful directory listing."""
        # Mock node_repo.get_by_id -> NodeInfo
        # Mock repo_repo.get_by_id -> RepoInfo
        # Mock node_client.list_directory -> entries
        
        result = await inspect_repo_tree_handler(
            node_id="node-1",
            repo_id="repo-1",
            path="src",
            node_client=mock_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )
        
        assert result["success"] is True
        assert "entries" in result
    
    async def test_unknown_node(self):
        """Test rejection of unknown node."""
        # Mock node_repo.get_by_id -> None
        
        result = await inspect_repo_tree_handler(
            node_id="unknown",
            repo_id="repo-1",
            node_client=mock_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    async def test_path_traversal_rejected(self):
        """Test path traversal is rejected."""
        # Path with ".." should fail validation
        
        result = await inspect_repo_tree_handler(
            node_id="node-1",
            repo_id="repo-1",
            path="../etc/passwd",
            node_client=mock_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )
        
        assert result["success"] is False
        assert "traversal" in result["error"].lower()


class TestReadRepoFile:
    """Tests for read_repo_file handler."""
    
    async def test_success(self):
        """Test successful file read."""
        # ... similar pattern
        
    async def test_unknown_repo(self):
        """Test rejection of unknown repo."""
        # ... 
```

### 10.2 Node Agent Tests

```python
# tests/node_agent/test_executor.py

import pytest
from pathlib import Path
import tempfile

from src.node_agent.executor import OperationExecutor


class TestOperationExecutor:
    """Tests for node agent executor."""
    
    @pytest.fixture
    def executor(self):
        """Create executor with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield OperationExecutor(allowed_paths=[tmpdir])
    
    async def test_list_directory(self, executor):
        """Test directory listing."""
        # Create test files
        # List directory
        # Verify entries
        
    async def test_read_file(self, executor):
        """Test file reading."""
        # Create test file
        # Read with offset/limit
        # Verify content
        
    async def test_path_traversal_blocked(self, executor):
        """Test path traversal is blocked."""
        with pytest.raises(PermissionError):
            await executor.read_file("/etc/passwd")
```

### 10.3 Integration Tests

- Test hub → node-agent communication with mock
- Test end-to-end path validation chain
- Test MCP tool response formatting

## 11. Acceptance Criteria Verification

| Criterion | Verification Method |
|-----------|---------------------|
| Repo tree inspection scoped to approved repos | Unit test: unknown repo returns error |
| File reads reject traversal | Unit test: ".." in path returns error |
| Responses structured for MCP | Response schema validation |

## 12. Integration Points

| From | To | Interface |
|------|-----|------------|
| MCP Protocol | inspect_repo_tree_handler | Tool call via PolicyAwareToolRouter |
| inspect_repo_tree_handler | HubNodeClient.list_directory() | NodeInfo + path |
| HubNodeClient | Node Agent /operations/list-dir | HTTP GET |
| Node Agent Executor | Filesystem | Bounded Path operations |

## 13. Risks and Assumptions

- **Assumption**: Node agents have network reachability via Tailscale
- **Risk**: Large directories may cause timeouts (mitigated with max_entries)
- **Risk**: Large files may cause memory issues (mitigated with limit parameter)
- **Risk**: Binary files will fail UTF-8 decode (documented limitation)

## 14. Blockers / Required Decisions

None - all required decisions are resolved:
- Policy engine already provides fail-closed behavior (CORE-005)
- Node client already exists (CORE-004)
- Tool routing framework already integrates policy (CORE-006)
- Path normalization already implemented (CORE-005)
