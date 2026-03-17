# WRITE-001 Implementation Plan: write_markdown with atomic scoped writes

## 1. Implementation Approach

The `write_markdown` tool will provide controlled markdown delivery to approved write roots with:
- **Write-target validation**: Uses existing `WriteTargetPolicy` from CORE-002 to validate target paths
- **Extension allowlist**: Enforces allowed extensions per registered write target
- **Content hashing**: SHA256 hash computed before/after write for verification
- **Atomic writes**: Temp file + rename pattern to ensure file integrity
- **Hub-to-node routing**: Hub validates, then dispatches to node agent for execution

## 2. Architecture Overview

```
[ChatGPT] -> [Hub MCP Handler] -> [PolicyAwareToolRouter]
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
              [Node Policy]        [WriteTargetPolicy]   [HubNodeClient]
                    |                     |
              [NodeRepository]    [WriteTargetRepository]
                    |
              [NodeAgent] -> [OperationExecutor.write_file()]
                                      |
                              [Atomic Write: temp + rename]
```

## 3. Implementation Components

### 3.1 Hub-Side Handler (src/hub/tools/markdown.py)

**File to create**: `src/hub/tools/markdown.py`

**Handler function**: `write_markdown_handler`

```python
async def write_markdown_handler(
    node_id: str,
    target_id: str,
    relative_path: str,
    content: str,
    mode: str = "create_or_overwrite",
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    write_repo: "WriteTargetRepository | None" = None,
) -> dict[str, Any]:
    """Write markdown content to an approved write target.
    
    Args:
        node_id: Target node identifier.
        target_id: Write target ID from the registry.
        relative_path: Path relative to write target root.
        content: Content to write.
        mode: Write mode - "create_or_overwrite" or "create_only".
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        write_repo: WriteTargetRepository for write target validation.
    
    Returns:
        Dict with success status, verification metadata, and file info.
    """
```

**Validation Flow**:
1. Validate node exists and is accessible
2. Validate write target exists and belongs to target
3. Extract extension from relative_path and validate against allowlist
4. Compute SHA256 hash of content
5. Call node agent via HubNodeClient.write_file()
6. Verify response includes verification metadata

### 3.2 Node Agent Implementation

**File to modify**: `src/node_agent/executor.py`

**New method**: `OperationExecutor.write_file()`

```python
async def write_file(self, path: str, content: str) -> dict:
    """Write content to a file (atomic write).
    
    Uses temp file + rename pattern for atomicity:
    1. Write to temp file (path.tmp)
    2. Compute SHA256 hash of temp file
    3. Rename temp to final path
    4. Verify final file hash matches
    
    Args:
        path: File path to write (must be validated)
        content: Content to write
    
    Returns:
        Dict with success, hash, bytes_written, verification status
    """
```

**Implementation details**:
- Use `os.replace()` for atomic rename (works on POSIX and Windows)
- Compute SHA256 before write (pre_hash) and after (post_hash)
- Return verification metadata: pre_hash, post_hash, verified (bool)
- Handle write errors gracefully with cleanup of temp file

### 3.3 Node Agent Route

**File to modify**: `src/node_agent/routes/operations.py`

**Existing stub to replace**: `write_file()` endpoint

```python
@router.post("/operations/write-file", response_model=OperationResponse)
async def write_file(request: WriteFileRequest) -> OperationResponse:
    """Write content to a file with atomic write and verification."""
```

**Request model already defined**: `WriteFileRequest` (line 56-60)

### 3.4 Policy Integration

**File to modify**: `src/hub/tool_routing/policy_router.py`

The `PolicyAwareToolRouter` already has logic to inject repositories to handlers. Need to verify `write_repo` is injected similarly to `node_repo` and `repo_repo`.

The policy requirement for write_markdown will use `WRITE_REQUIREMENT`:
- scope: OperationScope.WRITE
- requires_node: True
- requires_write_target: True

### 3.5 Tool Registration

**File to modify**: `src/hub/tools/__init__.py`

Add new registration function:
```python
def register_markdown_tools(registry: ToolRegistry) -> None:
    """Register markdown delivery tools."""
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.markdown import write_markdown_handler
    
    registry.register(
        ToolDefinition(
            name="write_markdown",
            description="Write markdown content to an approved write target...",
            handler=write_markdown_handler,
            parameters={...},
            policy=WRITE_REQUIREMENT,
        )
    )
```

And add to `register_all_tools()`.

## 4. New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/tools/markdown.py` | Hub-side write_markdown handler with validation logic |

## 5. Existing Files to Modify

| File | Changes |
|------|---------|
| `src/node_agent/executor.py` | Implement `write_file()` with atomic write + SHA256 verification |
| `src/node_agent/routes/operations.py` | Replace stub with actual implementation |
| `src/hub/tools/__init__.py` | Add `register_markdown_tools()` and call from `register_all_tools()` |
| `src/hub/dependencies.py` | Add DI provider for `write_repo` injection to handlers if needed |

## 6. Extension Allowlist Enforcement

**At Hub Level**:
- `WriteTargetPolicy.validate_write_access()` already checks extension against `target.allowed_extensions`
- Extension is extracted from relative_path and passed to policy

**At Node Level**:
- Node receives already-validated path
- Additional safety: node executor can optionally validate extension again using config

## 7. Content Hashing (SHA256)

**Hash computation**:
- Pre-write: Compute `hashlib.sha256(content.encode()).hexdigest()`
- Post-write: Read written file and compute hash
- Compare: `pre_hash == post_hash` indicates successful atomic write

**Response includes**:
```python
{
    "success": True,
    "path": "/target/docs/readme.md",
    "bytes_written": 1234,
    "content_hash": "sha256:abc123...",
    "verified": True,
    "mode": "create_or_overwrite"
}
```

## 8. Atomic Write Implementation

**Pattern**:
```python
import hashlib
import os
import tempfile

def atomic_write(path: str, content: str) -> dict:
    # Compute pre-write hash
    pre_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # Write to temp file
    dir_path = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(mode='w', dir=dir_path, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Atomic rename
        os.replace(tmp_path, path)
        
        # Post-write verification
        with open(path, 'rb') as f:
            post_hash = hashlib.sha256(f.read()).hexdigest()
        
        verified = (pre_hash == post_hash)
        
        return {
            "success": True,
            "pre_hash": pre_hash,
            "post_hash": post_hash,
            "verified": verified
        }
    except Exception:
        # Cleanup temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

## 9. Acceptance Criteria Verification

| Criterion | Verification Method |
|-----------|---------------------|
| Writes restricted to approved targets | WriteTargetPolicy.validate_write_access() called; unknown targets raise ValueError |
| Atomic write behavior explicit | os.replace() used; temp+rename pattern; verification hash returned |
| Write responses include verification metadata | Response includes content_hash, verified, bytes_written |

## 10. Validation Plan

1. **Static Analysis**: Run ruff linting on new files
2. **Unit Tests**: Test handler with mock node_client, verify policy calls
3. **Integration Test**: If runtime available, test hub->node->atomic write flow
4. **Edge Cases**:
   - Unknown target_id → ValueError from policy
   - Extension not in allowlist → ValueError from policy
   - Write to existing file (mode=create_only) → error response
   - Node unreachable → error from HubNodeClient

## 11. Dependencies on Existing Code

| Component | Source Ticket | Usage |
|-----------|---------------|-------|
| WriteTargetPolicy | CORE-002 | validate_write_access(path, extension) |
| HubNodeClient | CORE-004 | write_file(node, path, content) |
| PathNormalizer | CORE-005 | Path validation, extension extraction |
| PolicyAwareToolRouter | CORE-006 | WRITE_REQUIREMENT policy, DI injection |
| OperationExecutor | CORE-003 | _validate_path() for bounded execution |
| ToolRegistry/ToolDefinition | CORE-006 | Tool registration |

## 12. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Race condition in atomic write | Low | os.replace() is atomic on POSIX |
| Large file memory usage | Medium | Add size limit (e.g., 1MB) in handler |
| Hash collision | Very Low | SHA256 sufficient for verification |

## 13. No Blocking Decisions

All decisions resolved:
- Write-target model already exists (CORE-002)
- Node client already has write_file method (CORE-004)
- Policy framework supports WRITE scope (CORE-005, CORE-006)
- Atomic write pattern is standard and well-understood
