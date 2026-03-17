# Implementation Plan: CTX-002 - index_repo pipeline and content-hash tracking

## Overview

This plan defines the implementation for the `index_repo` pipeline that reads repository content, generates embeddings via the embedding service, and stores them in Qdrant with content-hash tracking for idempotent reindexing.

## 1. Indexing Pipeline Flow

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        index_repo Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│  1. Validate repo exists and user has access                       │
│  2. Fetch repo tree from node via HubNodeClient                     │
│  3. For each file:                                                  │
│     a. Read file content via HubNodeClient                         │
│     b. Compute SHA256 content hash                                  │
│     c. Check existing hash in Qdrant (by file_id)                   │
│     d. If hash unchanged → SKIP (log as unchanged)                 │
│     e. If hash changed or new → Generate embedding                  │
│        → Upsert to Qdrant (files collection)                        │
│  4. Detect deleted files (in Qdrant but not in repo)                │
│     → Delete from Qdrant                                            │
│  5. Update repo indexed status in SQLite                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

| Stage | Description | Key Components |
|-------|-------------|----------------|
| **1. Init** | Load repo, node, embedding service, Qdrant client | RepoRepository, HubNodeClient, EmbeddingServiceClient, QdrantClientWrapper |
| **2. Discovery** | Fetch current file list from node | `node_client.list_directory()` recursively |
| **3. Hash Check** | Compute content hashes and compare | SHA256, existing Qdrant payloads |
| **4. Embed & Upsert** | Generate embeddings for changed files | EmbeddingServiceClient.embed_batch() |
| **5. Cleanup** | Delete vectors for removed files | QdrantClientWrapper.delete_file() |
| **6. Finalize** | Mark repo as indexed with timestamp | RepoRepository.mark_indexed() |

## 2. Content-Hash Tracking Mechanism

### Hash Storage

Each file's content hash is stored in the Qdrant payload (Field: `content_hash`) as part of the `FileIndexPayload`:

```python
class FileIndexPayload(BaseModel):
    # ... existing fields ...
    content_hash: str = Field(..., description="SHA256 hash of file content")
```

### File ID Generation

File IDs are generated using a deterministic hash of the repo_id and relative path:

```python
def generate_file_id(repo_id: str, relative_path: str) -> str:
    """Generate unique file ID from repo and path.
    
    Args:
        repo_id: Repository identifier.
        relative_path: Relative path from repo root.
    
    Returns:
        Unique file identifier.
    """
    import hashlib
    # Use SHA256 for deterministic IDs
    key = f"{repo_id}:{relative_path}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]
```

### Hash Comparison Logic

When processing each file:

1. Read file content from node
2. Compute SHA256 hash of content
3. Query Qdrant for existing record by file_id
4. Compare new hash with stored `content_hash`:
   - **If equal**: Skip embedding generation, mark as unchanged
   - **If different or not found**: Generate embedding, upsert to Qdrant

## 3. Reindex Rules

### Idempotent Reindex Behavior

| Scenario | Action | Rationale |
|----------|--------|------------|
| **File unchanged** (hash matches) | Skip embedding, log `skipped_unchanged` | Avoid redundant embedding compute |
| **File changed** (hash differs) | Generate embedding, upsert to Qdrant | Update vector for new content |
| **File new** (no existing record) | Generate embedding, insert to Qdrant | First-time indexing |
| **File deleted** (in Qdrant, not in repo) | Delete from Qdrant | Clean up stale vectors |

### Batch Processing

Files are processed in configurable batches (default: 10) to balance memory usage and network calls:

```python
# Configuration for batch processing
INDEX_BATCH_SIZE: int = 10          # Files per embedding batch
INDEX_MAX_FILE_SIZE: int = 1_000_000  # Skip files > 1MB
INDEX_MAX_RETRIES: int = 3           # Retry failed embeddings
```

### Exclusion Rules

Files excluded from indexing:

- Binary files (detected by extension or content)
- Files > 1MB (configurable)
- Hidden files/directories (starting with `.`) - **except** `.gitignore`, `.env.example`
- Common non-code files: `node_modules/`, `__pycache__/`, `*.pyc`, `.git/`

## 4. Deleted and Changed File Handling

### Deleted File Detection

After processing all current files, the pipeline identifies deleted files by:

1. Query Qdrant for all files in the repo (filter by `repo_id`)
2. Compare with the current file list from the node
3. Files in Qdrant but not in current list → delete

```python
async def cleanup_deleted_files(
    qdrant_client: QdrantClientWrapper,
    repo_id: str,
    current_file_ids: set[str],
) -> list[str]:
    """Identify and delete vectors for files no longer in the repo.
    
    Args:
        qdrant_client: Qdrant client wrapper.
        repo_id: Repository ID to clean up.
        current_file_ids: Set of file IDs currently in the repo.
    
    Returns:
        List of deleted file IDs.
    """
    # Query all existing file IDs for this repo
    # (using scroll/pagination for large repos)
    existing_files = await qdrant_client.scroll_files(repo_id=repo_id)
    existing_ids = {f.id for f in existing_files}
    
    # Find deleted
    deleted_ids = existing_ids - current_file_ids
    
    # Delete from Qdrant
    for file_id in deleted_ids:
        await qdrant_client.delete_file(file_id)
    
    return list(deleted_ids)
```

### Changed File Handling

For changed files (hash differs):

1. Upsert new vector to Qdrant (replaces old vector with same file_id)
2. Log `indexed_changed` with old vs new hash (redacted)
3. Include metadata: `previous_hash` in the new payload for audit

### Incremental vs Full Reindex

The pipeline supports both modes:

- **Incremental** (default): Only process files changed since last index
- **Full**: Re-process entire repo (use when index is corrupted or on first setup)

```python
class IndexMode(StrEnum):
    INCREMENTAL = "incremental"  # Skip unchanged files
    FULL = "full"               # Re-index everything
```

## 5. Integration Points

### Qdrant Integration

Using existing `QdrantClientWrapper` from CTX-001:

| Method | Usage |
|--------|-------|
| `upsert_file(file_id, vector, payload)` | Insert/update file vectors |
| `delete_file(file_id)` | Remove deleted file vectors |
| `search_files()` | (For future cross-repo search) |
| `scroll_files(repo_id)` | Get all files for a repo (new method needed) |

### Embedding Service Integration

Using existing `EmbeddingServiceClient` from LLM-003:

```python
# Batch embedding for multiple files
result = await embedding_client.embed_batch(
    service=embedding_service,
    texts=[file_content_1, file_content_2, ...],
    encoding_format="float",
)

if result["success"]:
    embeddings = result["embeddings"]
    # Pair with file data and upsert to Qdrant
```

### Node Communication

Using existing `HubNodeClient` from REPO-002:

```python
# List all files recursively
async def get_all_files(node_client, node, repo_path):
    """Recursively list all files in a repo."""
    files = []
    entries = await node_client.list_directory(node, repo_path)
    for entry in entries:
        if entry["type"] == "file":
            files.append(entry["path"])
        elif entry["type"] == "directory":
            files.extend(await get_all_files(node_client, node, entry["path"]))
    return files

# Read file content
file_content = await node_client.read_file(node, file_path)
```

### SQLite Integration

Using existing `RepoRepository`:

```python
# Mark repo as indexed after successful pipeline
await repo_repo.mark_indexed(repo_id)

# Store index metadata
metadata = {
    "indexed_files": file_count,
    "skipped_files": skipped_count,
    "deleted_files": deleted_count,
    "duration_ms": duration,
    "indexed_at": datetime.utcnow().isoformat(),
}
```

## 6. New Files to Create

### `src/hub/services/indexing_pipeline.py`

Core indexing pipeline implementation:

```python
"""Repository indexing pipeline with content-hash tracking."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import FileIndexPayload, LLMServiceInfo, RepoInfo

logger = get_logger(__name__)


class IndexMode(StrEnum):
    INCREMENTAL = "incremental"
    FULL = "full"


@dataclass
class IndexResult:
    """Result of an indexing operation."""
    
    success: bool
    repo_id: str
    indexed_count: int = 0
    skipped_count: int = 0
    deleted_count: int = 0
    error: str | None = None
    duration_ms: int = 0


class IndexingPipeline:
    """Pipeline for indexing repository content into Qdrant.
    
    This pipeline reads repository files, generates embeddings, and stores
    them in Qdrant with content-hash tracking for idempotent reindexing.
    """
    
    # Configuration
    BATCH_SIZE: int = 10
    MAX_FILE_SIZE: int = 1_000_000
    MAX_RETRIES: int = 3
    
    # File extensions to index
    INDEXABLE_EXTENSIONS: set[str] = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
        ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
        ".kt", ".scala", ".md", ".txt", ".yaml", ".yml", ".json",
        ".toml", ".xml", ".sql", ".sh", ".bash", ".zsh",
    }
    
    # Directories to exclude
    EXCLUDED_DIRS: set[str] = {
        "node_modules", "__pycache__", ".git", ".svn", "venv",
        ".venv", "env", ".envirtual", "dist", "build", "target",
        ".next", ".nuxt", ".svelte", "coverage", ".pytest_cache",
    }
    
    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
        embedding_client: EmbeddingServiceClient,
        embedding_service: LLMServiceInfo,
    ):
        """Initialize the indexing pipeline.
        
        Args:
            qdrant_client: Qdrant client wrapper.
            embedding_client: Embedding service client.
            embedding_service: Embedding service configuration.
        """
        self._qdrant = qdrant_client
        self._embedding = embedding_client
        self._embedding_service = embedding_service
    
    async def index_repo(
        self,
        repo: RepoInfo,
        node_client: Any,  # HubNodeClient
        node_info: NodeInfo,
        mode: IndexMode = IndexMode.INCREMENTAL,
    ) -> IndexResult:
        """Index a repository into Qdrant.
        
        Args:
            repo: Repository to index.
            node_client: HubNodeClient for reading files.
            node_info: Node information for the repo host.
            mode: Indexing mode (incremental or full).
        
        Returns:
            IndexResult with operation statistics.
        """
        start = datetime.utcnow()
        indexed = 0
        skipped = 0
        deleted = 0
        
        try:
            # 1. Get all files from the repo
            files = await self._discover_files(node_client, node_info, repo.path)
            
            # 2. Process files
            current_file_ids = set()
            for batch in self._batch_files(files, self.BATCH_SIZE):
                batch_results = await self._process_batch(
                    batch, repo, node_client, node_info, mode
                )
                indexed += batch_results["indexed"]
                skipped += batch_results["skipped"]
                current_file_ids.update(batch_results["file_ids"])
            
            # 3. Cleanup deleted files (incremental mode only)
            if mode == IndexMode.INCREMENTAL:
                deleted = await self._cleanup_deleted(
                    repo.repo_id, current_file_ids
                )
            
            duration = int((datetime.utcnow() - start).total_seconds() * 1000)
            
            logger.info(
                "index_repo_success",
                repo_id=repo.repo_id,
                indexed=indexed,
                skipped=skipped,
                deleted=deleted,
                duration_ms=duration,
            )
            
            return IndexResult(
                success=True,
                repo_id=repo.repo_id,
                indexed_count=indexed,
                skipped_count=skipped,
                deleted_count=deleted,
                duration_ms=duration,
            )
            
        except Exception as e:
            logger.error("index_repo_failed", repo_id=repo.repo_id, error=str(e))
            return IndexResult(
                success=False,
                repo_id=repo.repo_id,
                error=str(e),
            )
    
    # ... additional methods (see full implementation)
```

### `src/hub/tools/indexing.py`

MCP tool handler for the `index_repo` tool:

```python
"""Index repository tool handler for MCP protocol."""

from typing import Any

from pydantic import BaseModel, Field

from src.hub.services.indexing_pipeline import IndexMode, IndexingPipeline
from src.shared.logging import get_logger
from src.shared.models import NodeInfo

logger = get_logger(__name__)


class IndexRepoParams(BaseModel):
    """Parameters for the index_repo tool."""
    
    repo_id: str = Field(..., description="Repository identifier to index")
    node_id: str | None = Field(None, description="Node ID (auto-detected from repo)")
    mode: str = Field(
        "incremental", description="Indexing mode: incremental or full"
    )
    force: bool = Field(
        False, description="Force reindex even if unchanged"
    )


async def index_repo_handler(
    params: IndexRepoParams,
    # Injected dependencies
    indexing_pipeline: IndexingPipeline | None = None,
    repo_repo: Any = None,
    node_repo: Any = None,
    node_client: Any = None,
) -> dict[str, Any]:
    """Index a repository's content into Qdrant.
    
    This tool reads repository files, generates embeddings, and stores
    them in Qdrant with content-hash tracking for idempotent reindexing.
    
    Args:
        params: Tool parameters.
        indexing_pipeline: IndexingPipeline instance.
        repo_repo: RepoRepository for repo lookup.
        node_repo: NodeRepository for node lookup.
        node_client: HubNodeClient for node communication.
    
    Returns:
        Dictionary with indexing results.
    """
    # Validate dependencies
    if not all([indexing_pipeline, repo_repo, node_repo, node_client]):
        return {"success": False, "error": "Required dependencies not available"}
    
    # Get repo
    repo = await repo_repo.get(params.repo_id)
    if not repo:
        return {"success": False, "error": f"Repository not found: {params.repo_id}"}
    
    # Get node
    node_id = params.node_id or repo.node_id
    node = await node_repo.get(node_id)
    if not node:
        return {"success": False, "error": f"Node not found: {node_id}"}
    
    # Build node info
    node_info = NodeInfo(
        node_id=node.node_id,
        hostname=node.hostname,
        name=node.name,
    )
    
    # Determine mode
    mode = IndexMode.FULL if params.mode == "full" else IndexMode.INCREMENTAL
    if params.force:
        mode = IndexMode.FULL
    
    # Run indexing
    result = await indexing_pipeline.index_repo(
        repo=repo,
        node_client=node_client,
        node_info=node_info,
        mode=mode,
    )
    
    # Update repo indexed status
    if result.success:
        await repo_repo.mark_indexed(repo.repo_id)
    
    return {
        "success": result.success,
        "repo_id": result.repo_id,
        "indexed_count": result.indexed_count,
        "skipped_count": result.skipped_count,
        "deleted_count": result.deleted_count,
        "duration_ms": result.duration_ms,
        "error": result.error,
    }
```

## 7. Existing Files to Modify

### `src/hub/services/qdrant_client.py`

Add new method for scrolling files by repo_id:

```python
async def scroll_files(
    self,
    repo_id: str,
    limit: int = 1000,
) -> list[Record]:
    """Scroll through all files for a specific repo.
    
    Args:
        repo_id: Repository ID to filter by.
        limit: Maximum records to return per scroll page.
    
    Returns:
        List of file records.
    """
    # Implementation uses scroll() with filter
```

### `src/hub/tools/__init__.py`

Register the new `index_repo` tool:

```python
from src.hub.tools.indexing import index_repo_handler, IndexRepoParams

TOOL_REGISTRY = {
    # ... existing tools ...
    "index_repo": {
        "handler": index_repo_handler,
        "params": IndexRepoParams,
        "description": "Index repository content into Qdrant for semantic search",
    },
}
```

### `src/hub/dependencies.py`

Add DI providers for the indexing pipeline:

```python
from src.hub.services.indexing_pipeline import IndexingPipeline

async def get_indexing_pipeline(
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
    embedding_client: EmbeddingServiceClient = Depends(get_embedding_client),
    llm_policy: LLMServicePolicy = Depends(get_llm_policy),
) -> IndexingPipeline:
    """Get indexing pipeline instance.
    
    Args:
        qdrant_client: Qdrant client wrapper.
        embedding_client: Embedding service client.
        llm_policy: LLM service policy.
    
    Returns:
        Initialized IndexingPipeline.
    """
    # Get embedding service from registry
    embedding_service = await llm_policy.get_service("embedding")
    if not embedding_service:
        raise RuntimeError("Embedding service not configured")
    
    return IndexingPipeline(
        qdrant_client=qdrant_client,
        embedding_client=embedding_client,
        embedding_service=embedding_service,
    )
```

### `src/shared/models.py`

Add helper function for file ID generation:

```python
def generate_file_id(repo_id: str, relative_path: str) -> str:
    """Generate unique file ID from repo and path.
    
    Args:
        repo_id: Repository identifier.
        relative_path: Relative path from repo root.
    
    Returns:
        Unique file identifier (32 hex chars).
    """
    import hashlib
    key = f"{repo_id}:{relative_path}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]
```

## 8. Validation Plan

### Unit Tests

| Test | Description |
|------|-------------|
| `test_hash_computation` | Verify SHA256 hash is consistent for same content |
| `test_file_id_generation` | Verify deterministic file IDs |
| `test_exclusion_rules` | Verify files are correctly excluded |
| `test_batch_processing` | Verify batch size handling |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_index_new_repo` | Index a new repo, verify all files indexed |
| `test_incremental_skip_unchanged` | Re-index, verify unchanged files skipped |
| `test_index_changed_file` | Modify file, verify new embedding generated |
| `test_delete_removed_file` | Delete file, verify Qdrant vector removed |
| `test_full_reindex` | Force full reindex, verify all files re-indexed |

### Validation Commands

```bash
# Run indexing tests
pytest tests/hub/services/test_indexing_pipeline.py -v

# Run tool handler tests
pytest tests/hub/tools/test_indexing.py -v

# Run linting
ruff check src/hub/services/indexing_pipeline.py src/hub/tools/indexing.py

# Type checking
mypy src/hub/services/indexing_pipeline.py src/hub/tools/indexing.py
```

## 9. Integration Points Summary

| Component | File | Integration |
|-----------|------|-------------|
| Qdrant | `qdrant_client.py` | `upsert_file()`, `delete_file()`, new `scroll_files()` |
| Embedding | `embedding_client.py` | `embed_batch()` for generating vectors |
| Node Client | `node_client.py` | `list_directory()`, `read_file()` |
| Repo Repository | `repos.py` | `mark_indexed()`, `get()` |
| LLM Policy | `llm_service_policy.py` | `get_service()` for embedding service lookup |
| Tool Router | `tools/__init__.py` | Register `index_repo` tool |
| DI | `dependencies.py` | Add `get_indexing_pipeline()` provider |

## 10. Risks and Assumptions

### Risks

| Risk | Mitigation |
|------|------------|
| Large repos cause memory pressure | Batch processing with configurable size |
| Network failures during indexing | Retry logic with exponential backoff |
| Embedding service unavailable | Fail gracefully, log error, partial results |
| Qdrant connection issues | Health check before operations, clear error messages |

### Assumptions

- Embedding service is configured and accessible (from LLM-003)
- Node agent is running and accessible (from CORE-003/004)
- Repo path is valid and accessible on the node (from REPO-002)
- Qdrant is running and initialized (from CTX-001)
- File content fits in memory (1MB limit enforced)

## 11. Acceptance Criteria

- [ ] **Pipeline flow explicit**: All 6 stages documented and implemented
- [ ] **Content-hash tracking**: SHA256 stored in Qdrant payload
- [ ] **Reindex rules defined**: Skip unchanged, update changed, delete removed
- [ ] **Deleted file handling**: Stale vectors removed from Qdrant
- [ ] **Changed file handling**: New embeddings generated, old vectors replaced
- [ ] **Qdrant integration**: Uses existing QdrantClientWrapper
- [ ] **Embedding integration**: Uses existing EmbeddingServiceClient
- [ ] **Node integration**: Uses existing HubNodeClient
- [ ] **Tool registered**: `index_repo` available via MCP
- [ ] **Tests pass**: Unit and integration tests validate behavior
