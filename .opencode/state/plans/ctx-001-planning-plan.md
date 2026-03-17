# CTX-001: Qdrant Integration and Context Storage Schema

## Overview

This plan defines the Qdrant integration, collection layout, and structured metadata schema for project context storage. The implementation follows existing GPTTalker patterns: service-based client wrapper, dependency injection, lifespan lifecycle management, and Pydantic model definitions.

## 1. Qdrant Client Integration Approach

### Architecture Pattern

The Qdrant client follows the same pattern as other hub services (e.g., `EmbeddingServiceClient`, `LLMServiceClient`):

- **Service class**: Wraps the raw `qdrant_client` with GPTTalker-specific logic
- **Async support**: Qdrant client is async-native; the wrapper preserves this
- **Lifecycle management**: Initialized in `lifespan.py`, stored in app state
- **DI integration**: Exposed via `dependencies.py` for FastAPI dependency injection

### Client Configuration

The existing `HubConfig` already defines Qdrant settings:

```python
# src/hub/config.py (already exists)
qdrant_host: str = Field("localhost", description="Qdrant server host")
qdrant_port: int = Field(6333, ge=1, le=65535, description="Qdrant server port")
```

Additional configuration options to add:

| Config Field | Type | Default | Description |
|---|---|---|---|
| `qdrant_grpc_port` | int | 6334 | gRPC port for faster operations |
| `qdrant_timeout` | float | 30.0 | Default request timeout in seconds |
| `qdrant_prefetch` | int | 100 | Default prefetch count for searches |
| `qdrant_collection_retain_seconds` | int | 7776000 | Default TTL for indexed vectors (90 days) |

### Collection Naming Convention

Collections follow a `{prefix}_{type}_{scope}` pattern:

| Collection | Purpose | Naming |
|---|---|---|
| File content | Indexed file contents for semantic search | `gpttalker_files` |
| Issues | Known issues with descriptions | `gpttalker_issues` |
| Code summaries | Extracted code summaries per file | `gpttalker_summaries` |

Rationale:
- Prefix `gpttalker_` avoids collisions with other Qdrant usage
- Plural naming (`files`, `issues`) indicates collections of items
- Lowercase with underscores matches Python/JSON conventions

## 2. Payload Schema for Indexed Files

### Vector Payload Structure

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any

class FileIndexPayload(BaseModel):
    """Payload for indexed file content in Qdrant."""
    
    # Identification
    file_id: str = Field(..., description="Unique file identifier (hash of path)")
    repo_id: str = Field(..., description="Repository this file belongs to")
    node_id: str = Field(..., description="Node hosting this repo")
    
    # File metadata
    path: str = Field(..., description="Absolute file path")
    relative_path: str = Field(..., description="Relative path from repo root")
    filename: str = Field(..., description="Filename without path")
    extension: str = Field(..., description="File extension (e.g., '.py', '.md')")
    
    # Content metadata
    content_hash: str = Field(..., description="SHA256 hash of file content")
    size_bytes: int = Field(..., description="File size in bytes")
    line_count: int = Field(..., description="Number of lines")
    language: str | None = Field(None, description="Detected language (e.g., 'python')")
    
    # Indexing metadata
    indexed_at: datetime = Field(..., description="Timestamp of indexing")
    indexed_by: str = Field(..., description="Who/what triggered indexing (trace_id)")
    
    # Searchable text (for hybrid search if needed)
    content_preview: str | None = Field(None, description="First N chars for preview")
    
    # Provenance
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
```

### Search-Specific Fields

For efficient filtering, the following payload fields are indexed as Qdrant "payload indexes":

| Field | Type | Filterable | Orderable |
|---|---|---|---|
| `repo_id` | keyword | ✅ | ❌ |
| `node_id` | keyword | ✅ | ❌ |
| `extension` | keyword | ✅ | ❌ |
| `content_hash` | keyword | ✅ | ❌ |
| `indexed_at` | datetime | ✅ | ✅ |
| `language` | keyword | ✅ | ❌ |
| `size_bytes` | integer | ✅ | ✅ |

## 3. Payload Schema for Issues

### Issue Vector Payload

```python
class IssueIndexPayload(BaseModel):
    """Payload for indexed issues in Qdrant."""
    
    # Identification
    issue_id: str = Field(..., description="Unique issue identifier (matches SQLite)")
    repo_id: str = Field(..., description="Repository this issue belongs to")
    
    # Issue content (semantic search target)
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description (full text)")
    
    # Status tracking
    status: str = Field(..., description="Issue status (open, in_progress, resolved, wontfix)")
    
    # Timestamps
    created_at: datetime = Field(..., description="Issue creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    indexed_at: datetime = Field(..., description="Timestamp of Qdrant indexing")
    
    # Provenance
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
```

### Indexable Fields

| Field | Type | Filterable | Orderable |
|---|---|---|---|
| `repo_id` | keyword | ✅ | ❌ |
| `status` | keyword | ✅ | ❌ |
| `created_at` | datetime | ✅ | ✅ |
| `updated_at` | datetime | ✅ | ✅ |
| `indexed_at` | datetime | ✅ | ✅ |

## 4. Collection Configuration

### Vector Size

- **Embedding dimension**: 1536 (OpenAI ada-002 compatible)
- **Distance metric**: Cosine (default for semantic search)
- **Quantization**: Scalar (optional, for storage optimization)

### Index Type

- **Primary index**: HNSW (Hierarchical Navigable Small World)
- **HNSW parameters**:
  - `m`: 16 (number of bidirectional links)
  - `ef_construct`: 128 (construction time/accuracy tradeoff)
  - `full_scan_threshold`: 10000 (point when full scan becomes cheaper)

## 5. New Files to Create

### Core Implementation

| File | Purpose |
|---|---|
| `src/hub/services/qdrant_client.py` | Qdrant client wrapper with async methods |
| `src/hub/services/context_collections.py` | Collection definitions and payload schemas |
| `src/hub/services/__init__.py` | Update exports |

### Configuration Updates

| File | Changes |
|---|---|
| `src/hub/config.py` | Add missing Qdrant config fields |
| `src/hub/dependencies.py` | Add DI provider for QdrantClient |
| `src/hub/lifespan.py` | Add Qdrant client initialization/shutdown |

### Data Model Updates

| File | Changes |
|---|---|
| `src/shared/models.py` | Add FileIndexPayload, IssueIndexPayload Pydantic models |

## 6. Existing Files to Modify

### Files Requiring Updates

| File | Modification |
|---|---|
| `src/hub/config.py` | Add qdrant_grpc_port, qdrant_timeout, qdrant_prefetch, qdrant_collection_retain_seconds |
| `src/hub/dependencies.py` | Add get_qdrant_client dependency provider |
| `src/hub/lifespan.py` | Add Qdrant client init in startup, close in shutdown |
| `src/hub/services/__init__.py` | Export QdrantClient and payload models |
| `src/shared/models.py` | Add FileIndexPayload, IssueIndexPayload classes |

## 7. Implementation Steps

### Step 1: Configuration Extensions

1. Add missing Qdrant config fields to `HubConfig`
2. Update `get_hub_config()` if needed

### Step 2: Payload Models

1. Add `FileIndexPayload` to `src/shared/models.py`
2. Add `IssueIndexPayload` to `src/shared/models.py`
3. Add any helper types/enums

### Step 3: Qdrant Client

1. Create `src/hub/services/qdrant_client.py`:
   - `QdrantClient` class with async methods:
     - `initialize()` - Create collections if not exist
     - `upsert_file()` - Add/update file vector
     - `upsert_issue()` - Add/update issue vector
     - `search_files()` - Semantic file search
     - `search_issues()` - Semantic issue search
     - `delete_file()` - Remove file vector
     - `delete_issue()` - Remove issue vector
     - `get_collection_info()` - Collection statistics
   - `get_qdrant_client()` factory function

2. Update `src/hub/services/__init__.py`

### Step 4: Dependency Injection

1. Add `get_qdrant_client()` to `src/hub/dependencies.py`:
   - Retrieve from app.state
   - Create new instance if not initialized
   - Return typed as `QdrantClient`

### Step 5: Lifecycle Integration

1. Update `src/hub/lifespan.py`:
   - Import QdrantClient
   - Add initialization in startup (after HTTP client)
   - Add shutdown cleanup (before HTTP client close)
   - Store in app.state

## 8. Validation Plan

### Unit Tests

1. **Config validation**: Verify Qdrant config fields parse correctly
2. **Payload models**: Verify FileIndexPayload/IssueIndexPayload serialization
3. **Client initialization**: Mock Qdrant server, verify connection

### Integration Tests

1. **Collection creation**: Test that collections are created with correct schema
2. **Upsert operations**: Test file and issue upsert with payload validation
3. **Search operations**: Test semantic search returns expected results
4. **Delete operations**: Test cleanup of vectors

### Manual Validation

1. Start local Qdrant container: `docker run -p 6333:6333 qdrant/qdrant`
2. Run hub with Qdrant enabled
3. Call health endpoint to verify client connectivity

## 9. Risks and Assumptions

### Risks

| Risk | Mitigation |
|---|---|
| Qdrant server unavailable at startup | Use fail-open: log warning, allow hub to start without vector search |
| Embedding service unavailable during indexing | Queue indexing operations, retry with backoff |
| Large repo causes memory pressure | Implement batched indexing with configurable batch size |

### Assumptions

| Assumption | Verification |
|---|---|
| Qdrant runs on same host as hub (default localhost:6333) | Document in deployment docs |
| Embedding service is registered before indexing | Indexing requires embedding service in llm_services table |
| Vector dimension is 1536 (OpenAI ada-002) | Configurable if different embedding model is used |

## 10. Integration Points

### With LLM-003 (Embedding Service)

- `QdrantClient.upsert_file()` calls `EmbeddingServiceClient.embed_batch()`
- Embedding service must be configured in llm_services table
- Timeout: 30s for embedding + 30s for Qdrant upsert

### With SETUP-003 (SQLite)

- `repos.is_indexed` flag updated after successful indexing
- `issues` table provides structured data; Qdrant provides semantic search
- No schema changes required to existing tables

### With Future Tickets

- **CTX-002**: Uses `QdrantClient.upsert_file()` for indexing
- **CTX-003**: Uses `QdrantClient.search_files()` / `search_issues()` for retrieval
- **XREPO-001**: Uses cross-repo search across `gpttalker_files` collection

## 11. Decision Blockers

None. All required architectural decisions have been resolved:

| Decision | Resolution |
|---|---|
| Qdrant client pattern | Follows existing service pattern (EmbeddingServiceClient) |
| Collection naming | `gpttalker_files`, `gpttalker_issues`, `gpttalker_summaries` |
| Vector dimension | 1536 (configurable if needed) |
| Distance metric | Cosine (standard for semantic search) |
| Index type | HNSW (default, good for most use cases) |

## 12. Acceptance Criteria Check

| Criterion | Status |
|---|---|
| Qdrant client pattern is defined | ✅ Addressed in Section 1, implemented in Step 3 |
| Collection naming is explicit | ✅ Addressed in Section 2 |
| Payload schema for indexed files is planned | ✅ Addressed in Section 2 |
| Payload schema for issues is planned | ✅ Addressed in Section 3 |
| New files to create are listed | ✅ Addressed in Section 5 |
| Existing files to modify are listed | ✅ Addressed in Section 6 |

---

**Plan prepared for CTX-001: Qdrant Integration and Context Storage Schema**
**Stage: Planning**
**Status: Ready for Review**
