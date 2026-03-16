# CORE-002: Implementation Plan - Repo, write-target, and LLM service registries

## Overview

Ticket CORE-002 defines structured registries for repos, markdown write targets, and LLM service aliases. These registries enable later tools to validate every target explicitly with fail-closed behavior.

**Current State**: The database schema (tables), Pydantic models, and repository classes already exist from SETUP-003:
- `src/shared/tables.py` - Tables `repos`, `write_targets`, `llm_services` defined
- `src/shared/models.py` - Models `RepoInfo`, `WriteTargetInfo`, `LLMServiceInfo` defined  
- `src/shared/repositories/` - Full CRUD repositories implemented

**Scope of CORE-002**: Add dependency injection providers and policy validation classes to make these registries usable by the MCP tool layer.

---

## 1. Scope

### 1.1 Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Repo registry model exists | ✅ Already exists in `src/shared/models.py` (RepoInfo) |
| 2 | Write-target registry model exists | ✅ Already exists in `src/shared/models.py` (WriteTargetInfo) |
| 3 | LLM service alias model exists | ✅ Already exists in `src/shared/models.py` (LLMServiceInfo) |
| 4 | DI providers expose repositories to FastAPI endpoints | Add to `src/hub/dependencies.py` |
| 5 | Fail-closed policy validation for repos | Create `src/hub/policy/repo_policy.py` |
| 6 | Fail-closed policy validation for write targets | Create `src/hub/policy/write_target_policy.py` |
| 7 | Fail-closed policy validation for LLM services | Create `src/hub/policy/llm_service_policy.py` |
| 8 | Policy DI providers | Add to `src/hub/dependencies.py` |

### 1.2 Files to Create

| File | Purpose |
|------|---------|
| `src/hub/policy/__init__.py` | Policy package exports |
| `src/hub/policy/repo_policy.py` | Repo access validation with fail-closed |
| `src/hub/policy/write_target_policy.py` | Write target and extension validation |
| `src/hub/policy/llm_service_policy.py` | LLM service alias validation |

### 1.3 Files to Modify

| File | Purpose |
|------|---------|
| `src/hub/dependencies.py` | Add DI providers for repositories and policies |

---

## 2. Schema Design (Already Implemented)

### 2.1 Repos Table

```sql
CREATE TABLE IF NOT EXISTS repos (
    repo_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    is_indexed INTEGER NOT NULL DEFAULT 0,
    indexed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);
```

### 2.2 Write Targets Table

```sql
CREATE TABLE IF NOT EXISTS write_targets (
    target_id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    path TEXT NOT NULL,
    allowed_extensions TEXT NOT NULL DEFAULT '[" .md",".txt"]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);
```

### 2.3 LLM Services Table

```sql
CREATE TABLE IF NOT EXISTS llm_services (
    service_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    endpoint TEXT,
    api_key TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);
```

---

## 3. Pydantic Models (Already Implemented)

### 3.1 RepoInfo

```python
class RepoInfo(BaseModel):
    repo_id: str
    name: str
    path: str
    node_id: str
    is_indexed: bool = False
```

### 3.2 WriteTargetInfo

```python
class WriteTargetInfo(BaseModel):
    target_id: str
    path: str
    allowed_extensions: list[str] = [".md", ".txt"]
```

### 3.3 LLMServiceInfo

```python
class LLMServiceInfo(BaseModel):
    service_id: str
    name: str
    type: LLMServiceType
    endpoint: str | None = None
    api_key: str | None = None
```

---

## 4. Repository Classes (Already Implemented)

### 4.1 RepoRepository (`src/shared/repositories/repos.py`)

| Method | Purpose |
|--------|---------|
| `create(repo, metadata)` | Insert new repo |
| `get(repo_id)` | Get by ID |
| `get_by_path(path)` | Get by path |
| `list_all()` | List all repos |
| `list_by_node(node_id)` | Filter by node |
| `list_indexed()` | Filter indexed repos |
| `update(repo, metadata)` | Update repo |
| `delete(repo_id)` | Delete repo |
| `mark_indexed(repo_id)` | Mark as indexed |
| `mark_unindexed(repo_id)` | Mark as not indexed |

### 4.2 WriteTargetRepository (`src/shared/repositories/write_targets.py`)

| Method | Purpose |
|--------|---------|
| `create(target, repo_id)` | Insert new write target |
| `get(target_id)` | Get by ID |
| `get_by_path(path)` | Get by path |
| `list_all()` | List all targets |
| `list_by_repo(repo_id)` | Filter by repo |
| `update(target, repo_id)` | Update target |
| `delete(target_id)` | Delete target |
| `is_path_allowed(path, extension)` | Check extension allowance |

### 4.3 LLMServiceRepository (`src/shared/repositories/llm_services.py`)

| Method | Purpose |
|--------|---------|
| `create(service, metadata)` | Insert new service |
| `get(service_id)` | Get by ID |
| `get_by_name(name)` | Get by name |
| `list_all()` | List all services |
| `list_by_type(service_type)` | Filter by type |
| `update(service, metadata)` | Update service |
| `delete(service_id)` | Delete service |

---

## 5. Implementation Steps

### Step 1: Create Policy Package

**File**: `src/hub/policy/__init__.py`

```python
"""Policy validation for GPTTalker registries."""

from src.hub.policy.repo_policy import RepoPolicy
from src.hub.policy.write_target_policy import WriteTargetPolicy
from src.hub.policy.llm_service_policy import LLMServicePolicy

__all__ = [
    "RepoPolicy",
    "WriteTargetPolicy",
    "LLMServicePolicy",
]
```

### Step 2: Create RepoPolicy

**File**: `src/hub/policy/repo_policy.py`

Purpose: Validate repo access with fail-closed behavior (reject unknown repos).

```python
"""Repo access policy with fail-closed validation."""

from src.shared.models import RepoInfo
from src.shared.repositories.repos import RepoRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class RepoPolicy:
    """Policy engine for repository access control."""

    def __init__(self, repo_repo: RepoRepository):
        """Initialize with repo repository.

        Args:
            repo_repo: Repository for repo CRUD operations.
        """
        self._repo = repo_repo

    async def validate_repo_access(self, repo_id: str) -> RepoInfo:
        """Validate access to a repository.

        Args:
            repo_id: Repository identifier to validate.

        Returns:
            RepoInfo if repository exists and is accessible.

        Raises:
            ValueError: If repository is unknown or inaccessible.
        """
        repo = await self._repo.get(repo_id)
        if not repo:
            logger.warning("repo_access_denied", repo_id=repo_id, reason="unknown_repo")
            raise ValueError(f"Unknown repository: {repo_id}")
        
        logger.info("repo_access_granted", repo_id=repo_id)
        return repo

    async def validate_path_in_repo(self, repo_id: str, file_path: str) -> bool:
        """Validate that a file path is within a repository.

        Args:
            repo_id: Repository identifier.
            file_path: Absolute file path to validate.

        Returns:
            True if path is within the repo, False otherwise.
        """
        repo = await self._repo.get(repo_id)
        if not repo:
            return False
        
        # Ensure path starts with repo path
        import os
        normalized_path = os.path.normpath(file_path)
        normalized_repo = os.path.normpath(repo.path)
        
        return normalized_path.startswith(normalized_repo)

    async def list_accessible_repos(self) -> list[RepoInfo]:
        """List all accessible repositories.

        Returns:
            List of all registered RepoInfo instances.
        """
        return await self._repo.list_all()

    async def list_repos_on_node(self, node_id: str) -> list[RepoInfo]:
        """List repositories on a specific node.

        Args:
            node_id: Node identifier to filter by.

        Returns:
            List of RepoInfo instances on the node.
        """
        return await self._repo.list_by_node(node_id)
```

### Step 3: Create WriteTargetPolicy

**File**: `src/hub/policy/write_target_policy.py`

Purpose: Validate write target access and extension allowlist enforcement.

```python
"""Write target policy with fail-closed validation."""

from src.shared.models import WriteTargetInfo
from src.shared.repositories.write_targets import WriteTargetRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class WriteTargetPolicy:
    """Policy engine for write target access control."""

    def __init__(self, write_repo: WriteTargetRepository):
        """Initialize with write target repository.

        Args:
            write_repo: Repository for write target CRUD operations.
        """
        self._repo = write_repo

    async def validate_write_access(self, path: str, extension: str) -> WriteTargetInfo:
        """Validate write access to a path.

        Args:
            path: Absolute path to write to.
            extension: File extension (e.g., '.md').

        Returns:
            WriteTargetInfo if path is allowed.

        Raises:
            ValueError: If path is unknown or extension not allowed.
        """
        target = await self._repo.get_by_path(path)
        if not target:
            logger.warning("write_access_denied", path=path, reason="unknown_target")
            raise ValueError(f"Unknown write target: {path}")
        
        if extension not in target.allowed_extensions:
            logger.warning(
                "write_access_denied",
                path=path,
                extension=extension,
                allowed=target.allowed_extensions,
                reason="extension_not_allowed"
            )
            raise ValueError(
                f"Extension '{extension}' not allowed. "
                f"Allowed: {target.allowed_extensions}"
            )
        
        logger.info("write_access_granted", path=path, extension=extension)
        return target

    async def list_write_targets(self) -> list[WriteTargetInfo]:
        """List all registered write targets.

        Returns:
            List of all WriteTargetInfo instances.
        """
        return await self._repo.list_all()

    async def list_write_targets_for_repo(self, repo_id: str) -> list[WriteTargetInfo]:
        """List write targets for a specific repository.

        Args:
            repo_id: Repository identifier to filter by.

        Returns:
            List of WriteTargetInfo instances for the repo.
        """
        return await self._repo.list_by_repo(repo_id)

    def validate_extension(self, extension: str, allowed: list[str]) -> bool:
        """Validate a file extension against an allowlist.

        Args:
            extension: File extension to validate.
            allowed: List of allowed extensions.

        Returns:
            True if extension is allowed.
        """
        return extension in allowed
```

### Step 4: Create LLMServicePolicy

**File**: `src/hub/policy/llm_service_policy.py`

Purpose: Validate LLM service alias access with fail-closed behavior.

```python
"""LLM service policy with fail-closed validation."""

from src.shared.models import LLMServiceInfo, LLMServiceType
from src.shared.repositories.llm_services import LLMServiceRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class LLMServicePolicy:
    """Policy engine for LLM service access control."""

    def __init__(self, llm_repo: LLMServiceRepository):
        """Initialize with LLM service repository.

        Args:
            llm_repo: Repository for LLM service CRUD operations.
        """
        self._repo = llm_repo

    async def validate_service_access(self, service_id: str) -> LLMServiceInfo:
        """Validate access to an LLM service.

        Args:
            service_id: Service identifier to validate.

        Returns:
            LLMServiceInfo if service exists and is accessible.

        Raises:
            ValueError: If service is unknown or inaccessible.
        """
        service = await self._repo.get(service_id)
        if not service:
            logger.warning(
                "llm_service_access_denied",
                service_id=service_id,
                reason="unknown_service"
            )
            raise ValueError(f"Unknown LLM service: {service_id}")
        
        logger.info("llm_service_access_granted", service_id=service_id)
        return service

    async def validate_service_by_name(self, name: str) -> LLMServiceInfo:
        """Validate access to an LLM service by name.

        Args:
            name: Service name to validate.

        Returns:
            LLMServiceInfo if service exists and is accessible.

        Raises:
            ValueError: If service is unknown or inaccessible.
        """
        service = await self._repo.get_by_name(name)
        if not service:
            logger.warning(
                "llm_service_access_denied",
                name=name,
                reason="unknown_service_name"
            )
            raise ValueError(f"Unknown LLM service name: {name}")
        
        logger.info("llm_service_access_granted", name=name)
        return service

    async def list_services(self) -> list[LLMServiceInfo]:
        """List all registered LLM services.

        Returns:
            List of all LLMServiceInfo instances.
        """
        return await self._repo.list_all()

    async def list_services_by_type(self, service_type: LLMServiceType) -> list[LLMServiceInfo]:
        """List LLM services of a specific type.

        Args:
            service_type: Type of service to filter by.

        Returns:
            List of LLMServiceInfo instances of the specified type.
        """
        return await self._repo.list_by_type(service_type)

    async def get_coding_agent_service(self) -> LLMServiceInfo | None:
        """Get the configured coding agent (OpenCode) service.

        Returns:
            LLMServiceInfo for OpenCode service, or None if not configured.
        """
        services = await self._repo.list_by_type(LLMServiceType.OPENCODE)
        return services[0] if services else None

    async def get_embedding_service(self) -> LLMServiceInfo | None:
        """Get the configured embedding service.

        Returns:
            LLMServiceInfo for embedding service, or None if not configured.
        """
        services = await self._repo.list_by_type(LLMServiceType.EMBEDDING)
        return services[0] if services else None
```

### Step 5: Update Dependencies

**File**: `src/hub/dependencies.py`

Add the following DI providers:

```python
from src.shared.repositories.repos import RepoRepository
from src.shared.repositories.write_targets import WriteTargetRepository
from src.shared.repositories.llm_services import LLMServiceRepository
from src.hub.policy.repo_policy import RepoPolicy
from src.hub.policy.write_target_policy import WriteTargetPolicy
from src.hub.policy.llm_service_policy import LLMServicePolicy


async def get_repo_repository(request: Request) -> RepoRepository:
    """Get repo repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        RepoRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return RepoRepository(db_manager)


async def get_write_target_repository(request: Request) -> WriteTargetRepository:
    """Get write target repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        WriteTargetRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return WriteTargetRepository(db_manager)


async def get_llm_service_repository(request: Request) -> LLMServiceRepository:
    """Get LLM service repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        LLMServiceRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return LLMServiceRepository(db_manager)


async def get_repo_policy(
    repo_repo: RepoRepository = Depends(get_repo_repository),
) -> RepoPolicy:
    """Get repo policy engine.

    Args:
        repo_repo: RepoRepository instance.

    Returns:
        RepoPolicy instance.
    """
    return RepoPolicy(repo_repo)


async def get_write_target_policy(
    write_repo: WriteTargetRepository = Depends(get_write_target_repository),
) -> WriteTargetPolicy:
    """Get write target policy engine.

    Args:
        write_repo: WriteTargetRepository instance.

    Returns:
        WriteTargetPolicy instance.
    """
    return WriteTargetPolicy(write_repo)


async def get_llm_service_policy(
    llm_repo: LLMServiceRepository = Depends(get_llm_service_repository),
) -> LLMServicePolicy:
    """Get LLM service policy engine.

    Args:
        llm_repo: LLMServiceRepository instance.

    Returns:
        LLMServicePolicy instance.
    """
    return LLMServicePolicy(llm_repo)
```

---

## 6. Integration with Later Tools

The registries will be used by these dependent tickets:

| Ticket | Registry Usage |
|--------|----------------|
| CORE-005 | Policy engine uses these policies for validation |
| CORE-006 | MCP tool routing uses repositories to validate targets |
| REPO-001 | `list_repos` tool uses RepoRepository |
| REPO-002 | `inspect_repo_tree`, `read_repo_file` validate repo access via RepoPolicy |
| WRITE-001 | `write_markdown` validates via WriteTargetPolicy |
| LLM-001 | `chat_llm` validates service via LLMServicePolicy |
| CTX-002 | `index_repo` uses RepoRepository |
| XREPO-002 | Tracks repo relationships |

---

## 7. Validation Plan

### 7.1 Code Quality

- [ ] All new files pass `ruff check`
- [ ] All new files pass `ruff format`
- [ ] Type hints complete on all new functions
- [ ] Docstrings present on all public classes and functions

### 7.2 Unit Tests

| Test | Description |
|------|-------------|
| `test_repo_policy_validates_unknown` | Verify unknown repo raises ValueError |
| `test_repo_policy_validates_path` | Verify path containment check works |
| `test_write_target_policy_validates_extension` | Verify extension allowlist enforcement |
| `test_write_target_policy_rejects_unknown` | Verify unknown path raises ValueError |
| `test_llm_service_policy_validates_unknown` | Verify unknown service raises ValueError |
| `test_llm_service_policy_get_by_name` | Verify name-based lookup works |
| `test_policy_di_providers` | Verify DI providers return policy instances |

### 7.3 Integration Tests

- [ ] Database migrations apply cleanly (schema v2 already current)
- [ ] Repository DI providers work in FastAPI endpoints
- [ ] Policy DI providers work in FastAPI endpoints
- [ ] Fail-closed behavior confirmed for all three registries

---

## 8. Risks and Assumptions

### 8.1 Risks

| Risk | Mitigation |
|------|------------|
| Repository classes not fully CRUD | Already implemented, verified via code review |
| Schema migration may need adjustment | Tables created in v1, no migration needed |

### 8.2 Assumptions

| Assumption | Notes |
|------------|-------|
| Database is initialized before policy use | Hub lifespan handles this |
| Node registry exists before repo registry | CORE-001 dependency satisfied |
| Fail-closed is the correct default | Per canonical brief security rules |

---

## 9. Blockers and Decisions

### 9.1 Required Decisions

None - all acceptance criteria have clear implementation paths.

### 9.2 No Blockers

The ticket dependencies (SETUP-003, SETUP-004) are complete, and the required infrastructure already exists.

---

## 10. Migration Status

**Current Schema Version**: 2 (from CORE-001)

The three registry tables (`repos`, `write_targets`, `llm_services`) were created in schema version 1 (SETUP-003). No additional migration is required for CORE-002.
