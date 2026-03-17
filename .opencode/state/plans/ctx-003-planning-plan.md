# CTX-003 Implementation Plan: get_project_context and known-issue records

## 1. Scope

This ticket implements two MCP tools for semantic project context retrieval and structured known-issue management:

1. **get_project_context**: Semantic search over indexed repository content with full provenance metadata
2. **record_issue**: Create and index structured issue records for semantic search

## 2. Context Retrieval Approach

### get_project_context Tool

The tool will perform semantic search over indexed files in Qdrant using query embeddings:

- **Input**: Natural language query string, optional repo_id filter, optional node_id filter
- **Process**: 
  1. Generate embedding for the query using the configured embedding service
  2. Search Qdrant's `gpttalker_files` collection with similarity search
  3. Apply repo_id/node_id filters if provided
  4. Return results with full provenance metadata from the stored payloads

### Provenance Metadata in Responses

Each search result will include provenance fields from `FileIndexPayload`:

| Field | Source | Description |
|-------|--------|-------------|
| `file_id` | FileIndexPayload | Unique file identifier |
| `repo_id` | FileIndexPayload | Repository identifier |
| `node_id` | FileIndexPayload | Node hosting the repo |
| `path` | FileIndexPayload | Absolute file path |
| `relative_path` | FileIndexPayload | Path relative to repo root |
| `filename` | FileIndexPayload | Filename without path |
| `extension` | FileIndexPayload | File extension |
| `content_hash` | FileIndexPayload | SHA256 of content |
| `language` | FileIndexPayload | Detected language |
| `indexed_at` | FileIndexPayload | When file was indexed |
| `score` | Qdrant | Similarity score |

### Known-Issue Schema

The issue system uses existing models:

**SQLite Schema (IssueRecord from models.py)**:
- `issue_id`: UUID - Unique identifier
- `repo_id`: str - Repository this issue belongs to  
- `title`: str - Issue title
- `description`: str - Full issue description
- `status`: IssueStatus (OPEN, IN_PROGRESS, RESOLVED, WONT_FIX)
- `created_at`: datetime - Creation timestamp
- `updated_at`: datetime | None - Last update
- `metadata`: dict - Additional metadata

**Qdrant Schema (IssueIndexPayload from models.py)**:
- `issue_id`: str - Unique identifier (matches SQLite)
- `repo_id`: str - Repository this issue belongs to
- `title`: str - Issue title (semantic search target)
- `description`: str - Full text description
- `status`: str - Issue status
- `created_at`: datetime - Creation timestamp
- `updated_at`: datetime | None - Last update
- `indexed_at`: datetime - When indexed to Qdrant
- `metadata`: dict - Additional metadata

## 3. Repo Access Checks

Both tools require **READ_REPO_REQUIREMENT** policy validation:

- `get_project_context`: Requires valid node + repo access; repo_id filter must match approved repos
- `record_issue`: Requires valid node + repo access; issues are created for approved repos only

The policy integration ensures:
- Unknown repos are rejected explicitly (fail-closed)
- Node access is validated before any operation
- Access control is centralized in PolicyAwareToolRouter

## 4. New Files to Create

### 4.1 `src/hub/tools/context.py`

New tool handlers for context retrieval and issue management:

```python
# Key exports:
class GetProjectContextParams(BaseModel):
    """Parameters for get_project_context tool."""
    query: str = Field(..., description="Natural language search query")
    repo_id: str | None = Field(None, description="Filter by specific repository")
    node_id: str | None = Field(None, description="Filter by specific node")
    limit: int = Field(10, description="Maximum results", ge=1, le=100)
    score_threshold: float | None = Field(None, description="Minimum similarity score")

class RecordIssueParams(BaseModel):
    """Parameters for record_issue tool."""
    repo_id: str = Field(..., description="Repository identifier")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    status: str = Field("open", description="Issue status")
    metadata: dict | None = Field(None, description="Additional metadata")

# Handlers:
async def get_project_context_handler(params: GetProjectContextParams, ...) -> dict
async def record_issue_handler(params: RecordIssueParams, ...) -> dict
```

### 4.2 Additional Schema Definitions

Add to `src/shared/schemas.py`:

```python
class GetProjectContextResponse(BaseModel):
    """Response for get_project_context tool."""
    query: str = Field(..., description="Original search query")
    results: list[ContextSearchResult] = Field(default_factory=list)
    total: int = Field(..., description="Total matches found")
    repo_id: str | None = Field(None, description="Filter used")
    latency_ms: int = Field(..., description="Search latency")

class ContextSearchResult(BaseModel):
    """Single context search result with provenance."""
    file_id: str
    repo_id: str
    node_id: str
    path: str
    relative_path: str
    filename: str
    extension: str
    language: str | None
    content_hash: str
    size_bytes: int
    line_count: int
    indexed_at: datetime
    score: float
    content_preview: str | None

class RecordIssueResponse(BaseModel):
    """Response for record_issue tool."""
    success: bool
    issue_id: str
    repo_id: str
    title: str
    indexed: bool = Field(..., description="Whether issue was indexed in Qdrant")
    error: str | None = None
```

## 5. Existing Files to Modify

### 5.1 `src/shared/schemas.py`
- Add `GetProjectContextParams`, `GetProjectContextResponse`, `ContextSearchResult`, `RecordIssueParams`, `RecordIssueResponse` schemas

### 5.2 `src/hub/tools/__init__.py`
- Add import for new context handlers
- Register `get_project_context` and `record_issue` tools in `register_context_tools()`
- Apply `READ_REPO_REQUIREMENT` policy to both tools

### 5.3 `src/hub/dependencies.py`
- Add `get_issue_repository` dependency provider (for SQLite issue CRUD)
- The Qdrant client is already available via `get_qdrant_client`

### 5.4 `src/shared/schemas.py` - ToolName enum
- Add `GET_PROJECT_CONTEXT = "get_project_context"` 
- Add `RECORD_ISSUE = "record_issue"`

## 6. Implementation Steps

### Step 1: Add Schema Definitions
- Add request/response schemas to `src/shared/schemas.py`
- Add tool names to `ToolName` enum

### Step 2: Create Context Tool Handlers
- Create `src/hub/tools/context.py` with:
  - `GetProjectContextParams` and `RecordIssueParams` models
  - `get_project_context_handler`: Generates query embedding, searches Qdrant files, returns with provenance
  - `record_issue_handler`: Creates SQLite record, generates embedding, indexes to Qdrant issues

### Step 3: Register Tools
- Import handlers in `src/hub/tools/__init__.py`
- Register `get_project_context` tool with:
  - Policy: `READ_REPO_REQUIREMENT`
  - Parameters: query, repo_id (optional), node_id (optional), limit, score_threshold
- Register `record_issue` tool with:
  - Policy: `READ_REPO_REQUIREMENT`
  - Parameters: repo_id, title, description, status, metadata

### Step 4: Add DI Provider
- Add `get_issue_repository` to `src/hub/dependencies.py`
- Ensure dependencies are passed to policy router

### Step 5: Testing
- Unit tests for schema validation
- Unit tests for handler logic (mock Qdrant client)
- Integration tests for tool registration and policy enforcement

## 7. Validation Plan

### Acceptance Criteria Verification

1. **Context retrieval returns provenance metadata**
   - Verify response includes all provenance fields: file_id, repo_id, node_id, path, relative_path, filename, extension, content_hash, language, indexed_at, score

2. **Known-issue records have a structured schema**
   - Verify SQLite storage via IssueRepository
   - Verify Qdrant indexing via IssueIndexPayload
   - Verify status enum validation (open, in_progress, resolved, wontfix)

3. **Repo access checks still apply**
   - Policy validation via PolicyAwareToolRouter
   - Unknown repo_id returns explicit rejection
   - Filter by repo_id restricts results to approved repos only

### Validation Commands

```bash
# Lint check
ruff check src/hub/tools/context.py src/shared/schemas.py

# Type check  
python -m py_compile src/hub/tools/context.py src/shared/schemas.py

# Import check
python -c "from src.hub.tools.context import get_project_context_handler, record_issue_handler"
```

## 8. Risks and Assumptions

### Risks
- **Qdrant search latency**: Large result sets may impact response time; limit parameter enforced (max 100)
- **Embedding service availability**: Tool fails gracefully if embedding service unavailable

### Assumptions
- Embedding service is configured and accessible (required for semantic search)
- Qdrant collections exist from CTX-001/002
- SQLite issues table exists from SETUP-003
- Policy engine integration works as designed in CORE-006

## 9. Integration Points

| Component | Integration Point | Verification |
|-----------|------------------|--------------|
| QdrantClientWrapper | Use existing `search_files()` method | Unit test with mock |
| EmbeddingServiceClient | Generate query embeddings | Unit test with mock |
| IssueRepository | Create/read issues in SQLite | Unit test with mock |
| PolicyAwareToolRouter | Policy validation | Integration test |
| ToolRegistry | Tool registration | Tool discovery test |

## 10. Blockers and User Decisions

No blocking decisions remain. All required components are in place:
- Qdrant client exists from CTX-001
- Indexing pipeline exists from CTX-002  
- Embedding client exists from LLM-003
- Policy framework exists from CORE-006
- Issue repository exists from SETUP-003

The implementation can proceed immediately.
