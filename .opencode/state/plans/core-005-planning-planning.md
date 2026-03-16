# CORE-005: Policy Engine and Normalized Path Validation

## Implementation Plan

### 1. Overview

Ticket CORE-005 builds the **fail-closed policy engine orchestration layer** and **centralized path normalization utility**. This work integrates the individual policy classes from CORE-001/CORE-002 into a unified validation chain that enforces security boundaries before any tool executes.

**Dependencies**: SETUP-002 (shared schemas, config, logging), SETUP-004 (FastAPI hub shell), CORE-001 (NodePolicy, NodeHealthService), CORE-002 (RepoPolicy, WriteTargetPolicy, LLMServicePolicy)

### 2. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Unknown targets are rejected explicitly | Policy engine returns clear rejection reasons for unknown nodes/repos/services |
| 2 | Path normalization rules are central and reusable | `PathNormalizer` utility in shared location, used by all path-validating code |
| 3 | Write and read scopes are separated cleanly | Separate validation methods for read vs write operations in the orchestration layer |

### 3. Architecture

#### 3.1 New Components

```
src/hub/policy/
├── __init__.py           # Update exports
├── path_utils.py         # NEW: Central path normalization
├── engine.py             # NEW: Policy orchestration layer
└── scopes.py             # NEW: Read/write scope definitions
```

#### 3.2 Integration Points

- **Dependencies** (`src/hub/dependencies.py`): Add DI provider for `PolicyEngine`
- **Tool Router** (`src/hub/tool_router.py`): Connect policy engine to routing (CORE-006 will complete this)
- **Exceptions** (`src/shared/exceptions.py`): Already has `PathTraversalError`, `PolicyViolationError`

### 4. Implementation Details

#### 4.1 Path Normalization Utility (`src/hub/policy/path_utils.py`)

Create a central utility that all path validation flows use:

```python
class PathNormalizer:
    """Central path normalization and validation.
    
    Enforces:
    - No path traversal (..)
    - No symlink escapes
    - No absolute paths (relative to base)
    - Normalized separators
    """
    
    @staticmethod
    def normalize(path: str, base: str | None = None) -> str:
        """Normalize a path relative to base.
        
        Args:
            path: The path to normalize.
            base: Optional base directory.
            
        Returns:
            Normalized path.
            
        Raises:
            PathTraversalError: If path escapes base.
        """
    
    @staticmethod
    def validate_no_traversal(path: str) -> bool:
        """Check for path traversal attempts.
        
        Returns True if safe, raises PathTraversalError if dangerous.
        """
    
    @staticmethod
    def is_safe_relative(path: str, base: str) -> bool:
        """Verify path stays within base directory.
        """
```

**PathValidationResult return type**:

```python
@dataclass
class PathValidationResult:
    """Result of path validation operations."""
    
    normalized_path: str
    is_valid: bool
    error: str | None = None
```

**Key rules**:
- Reject any path containing `..` components after normalization
- Reject symlinks that escape the base (resolve and compare)
- Normalize to forward slashes for consistency
- Strip leading/trailing whitespace

#### 4.2 Scope Definitions (`src/hub/policy/scopes.py`)

Define operation scopes for clean separation:

```python
class OperationScope:
    """Defines the type of operation being performed."""
    
    READ = "read"      # Read-only operations
    WRITE = "write"    # Write operations
    EXECUTE = "execute"  # Execution operations

@dataclass
class ValidationContext:
    """Context for policy validation."""
    scope: OperationScope
    trace_id: str | None
    caller: str | None  # Source of the request
```

#### 4.3 Policy Engine Orchestration (`src/hub/policy/engine.py`)

Create the main orchestration layer that combines all policies:

```python
@dataclass
class ValidationResult:
    """Result of policy validation operations.
    
    Attributes:
        allowed: Whether the operation is allowed.
        reason: Human-readable reason for the result (None if allowed).
        scope: The operation scope that was validated.
    """
    
    allowed: bool
    reason: str | None
    scope: OperationScope


class PolicyEngine:
    """Unified policy engine combining all policy checks.
    
    Implements fail-closed validation chain:
    1. Node access validation
    2. Repository access validation  
    3. Path normalization (for file operations)
    4. Write target validation (for writes)
    5. LLM service validation (for LLM operations)
    
    Each step must pass before proceeding.
    """
    
    def __init__(
        self,
        node_policy: NodePolicy,
        repo_policy: RepoPolicy,
        write_target_policy: WriteTargetPolicy,
        llm_service_policy: LLMServicePolicy,
    ):
        self.node_policy = node_policy
        self.repo_policy = repo_policy
        self.write_target_policy = write_target_policy
        self.llm_service_policy = llm_service_policy
    
    # Read operation validators
    async def validate_node_read(self, node_id: str) -> NodeAccessResult
    async def validate_repo_read(self, repo_id: str) -> RepoInfo
    async def validate_file_read(self, node_id: str, repo_id: str, file_path: str) -> PathValidationResult
    
    # Write operation validators  
    async def validate_node_write(self, node_id: str) -> NodeAccessResult
    async def validate_write_target(self, path: str, extension: str) -> WriteTargetInfo
    async def validate_file_write(self, node_id: str, repo_id: str, file_path: str, extension: str) -> PathValidationResult
    
    # LLM operation validators
    async def validate_llm_service(self, service_id: str) -> LLMServiceInfo
    
    # Combined validation chains
    async def validate_read_operation(
        self, 
        context: ValidationContext,
        node_id: str,
        repo_id: str | None = None,
        file_path: str | None = None,
    ) -> ValidationResult
    
    async def validate_write_operation(
        self,
        context: ValidationContext,
        node_id: str,
        path: str,
        extension: str,
    ) -> ValidationResult
```

**Fail-closed behavior**:
- Any unknown node/repo/service → explicit rejection with reason
- Path validation failure → `PathTraversalError`
- Write to unregistered target → `WriteTargetNotAllowedError`
- Missing required parameters → `ValidationError`
- All rejections include structured logging with trace_id

#### 4.4 Update Policy Module Init (`src/hub/policy/__init__.py`)

Export new components:

```python
from src.hub.policy.path_utils import PathNormalizer, PathValidationResult
from src.hub.policy.scopes import OperationScope, ValidationContext
from src.hub.policy.engine import PolicyEngine, ValidationResult

__all__ = [
    "PathNormalizer",
    "PathValidationResult",
    "OperationScope", 
    "ValidationContext",
    "PolicyEngine",
    "ValidationResult",
    # Re-export existing policies
    "NodePolicy",
    "RepoPolicy", 
    "WriteTargetPolicy",
    "LLMServicePolicy",
]
```

#### 4.5 Add DI Provider (`src/hub/dependencies.py`)

Add policy engine dependency:

```python
async def get_policy_engine(
    node_policy: NodePolicy = Depends(get_node_policy),
    repo_policy: RepoPolicy = Depends(get_repo_policy),
    write_target_policy: WriteTargetPolicy = Depends(get_write_target_policy),
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),
) -> PolicyEngine:
    """Get the unified policy engine.
    
    Args:
        node_policy: NodePolicy instance.
        repo_policy: RepoPolicy instance.
        write_target_policy: WriteTargetPolicy instance.
        llm_service_policy: LLMServicePolicy instance.
        
    Returns:
        PolicyEngine instance.
    """
    return PolicyEngine(
        node_policy=node_policy,
        repo_policy=repo_policy,
        write_target_policy=write_target_policy,
        llm_service_policy=llm_service_policy,
    )
```

### 5. File List

| File | Action | Description |
|------|--------|-------------|
| `src/hub/policy/path_utils.py` | CREATE | Central path normalization utility |
| `src/hub/policy/scopes.py` | CREATE | Operation scope definitions |
| `src/hub/policy/engine.py` | CREATE | Policy orchestration layer |
| `src/hub/policy/__init__.py` | MODIFY | Add exports for new modules |
| `src/hub/dependencies.py` | MODIFY | Add `get_policy_engine` dependency |
| `src/shared/exceptions.py` | REVIEW | Already has needed exceptions |

### 6. Validation Plan

#### 6.1 Unit Tests

| Component | Test Coverage |
|-----------|---------------|
| PathNormalizer | Path traversal rejection, symlink escape detection, base containment |
| PathValidationResult | Valid/invalid path result construction |
| ValidationResult | Allowed/rejected result construction |
| PolicyEngine.read | Unknown node/repo rejection, valid read approval |
| PolicyEngine.write | Unknown target rejection, extension validation, scope separation |
| Integration | Full validation chain with logging |

#### 6.2 Validation Commands

```bash
# Lint
ruff check src/hub/policy/

# Type check  
ruff check src/hub/policy/ --select=F

# Tests
pytest tests/hub/policy/ -v
```

### 7. Integration Points

| Later Ticket | Integration |
|-------------|-------------|
| CORE-006 | Tool router calls `PolicyEngine` before executing tools |
| REPO-002 | Uses `PathNormalizer` for file read validation |
| WRITE-001 | Uses `PolicyEngine.validate_write_operation()` |
| LLM-001 | Uses `PolicyEngine.validate_llm_service()` |

### 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Path normalization edge cases | Medium | Comprehensive test cases for symlinks, edge paths |
| Performance of validation chain | Low | Individual policies are lightweight; no significant overhead |
| Integration with existing policies | Medium | New engine delegates to existing classes; no behavior changes |

### 9. Assumptions

1. Individual policy classes (NodePolicy, RepoPolicy, etc.) are already tested and stable
2. The `trace_id` context is available via `src.shared.context` module
3. Exception hierarchy in `src.shared.exceptions` is sufficient for policy violations
4. DI pattern in `dependencies.py` is the correct approach for the hub

### 10. Blocker Checklist

- [x] SETUP-002: Shared schemas and logging — DONE
- [x] SETUP-004: FastAPI hub shell — DONE  
- [x] CORE-001: NodePolicy, NodeHealthService — DONE
- [x] CORE-002: RepoPolicy, WriteTargetPolicy, LLMServicePolicy — DONE

**No blocking decisions remain.** All required dependencies are complete.

(End of file - total 330 lines)
