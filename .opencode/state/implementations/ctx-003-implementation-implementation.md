# CTX-003 Implementation Summary: get_project_context and known-issue records

## Overview

This ticket implements two MCP tools for semantic project context retrieval and structured known-issue management:

1. **get_project_context**: Semantic search over indexed repository content with full provenance metadata
2. **record_issue**: Create and index structured issue records for semantic search

## Changes Made

### New Files Created

#### 1. `src/hub/tools/context.py`
- Created tool handlers for context retrieval and issue management
- `GetProjectContextParams` and `RecordIssueParams` Pydantic models
- `get_project_context_handler`: Generates query embedding, searches Qdrant files, returns with provenance
- `record_issue_handler`: Creates SQLite record, generates embedding, indexes to Qdrant issues
- Full error handling and structured logging
- **SECURITY FIX**: Added access control for global search (repo_id=None)

### Modified Files

#### 2. `src/shared/schemas.py`
- Added `GetProjectContextParams` schema
- Added `ContextSearchResult` schema with all provenance fields
- Added `GetProjectContextResponse` schema
- Added `RecordIssueParams` schema
- Added `RecordIssueResponse` schema

#### 3. `src/hub/tools/__init__.py`
- Updated `register_context_tools()` to include new tool registrations
- Registered `get_project_context` tool with:
  - Policy: `READ_REPO_REQUIREMENT`
  - Parameters: query (required), repo_id, node_id, limit, score_threshold
- Registered `record_issue` tool with:
  - Policy: `READ_REPO_REQUIREMENT`
  - Parameters: repo_id, title, description, status, metadata

#### 4. `src/hub/dependencies.py`
- Added import for `IssueRepository`
- Added `get_issue_repository` dependency provider
- Added `get_llm_service_client` dependency provider
- Added `get_embedding_service_client` dependency provider
- Updated `get_policy_aware_router` to inject:
  - `qdrant_client`
  - `embedding_client`
  - `issue_repo`

#### 5. `src/hub/tool_routing/policy_router.py`
- Added TYPE_CHECKING imports for new dependency types
- Updated `PolicyAwareToolRouter.__init__` to accept:
  - `qdrant_client: QdrantClientWrapper | None`
  - `embedding_client: EmbeddingServiceClient | None`
  - `issue_repo: IssueRepository | None`
- Updated `_execute_handler` to inject new dependencies to handlers

#### 6. `src/hub/services/qdrant_client.py`
- **SECURITY FIX**: Added `repo_ids` parameter to `search_files()` method
- Supports filtering by list of repo_ids for access control
- Uses Qdrant `should` conditions for OR logic across multiple repo_ids

## Implementation Details

### get_project_context Tool
- Accepts natural language query, optional repo_id/node_id filters, limit, score_threshold
- Generates query embedding using configured embedding service
- Performs semantic search over Qdrant's `gpttalker_files` collection
- Returns results with full provenance metadata:
  - file_id, repo_id, node_id, path, relative_path, filename, extension
  - content_hash, language, size_bytes, line_count, indexed_at
  - score (similarity), content_preview

### record_issue Tool
- Accepts repo_id, title, description, status, metadata
- Validates status enum (open, in_progress, resolved, wontfix)
- Creates issue record in SQLite via IssueRepository
- Generates embedding for issue content
- Indexes issue in Qdrant's `gpttalker_issues` collection
- Returns success status, issue_id, and indexed flag

### Security Fix: Global Search Access Control

**Issue Fixed**: Global search (repo_id=None) was bypassing repo-level access control, returning results from ALL indexed repos regardless of user permissions.

**Solution**:
1. When `repo_id` is None (global search), retrieve list of accessible repos from `RepoRepository.list_all()`
2. Pass the list of accessible repo_ids to Qdrant search via new `repo_ids` parameter
3. Qdrant filters results using OR logic across the provided repo_ids
4. If repo_repo is unavailable, global search returns an error (fail-closed)

**Code Changes**:
- `context.py`: Added `accessible_repo_ids` logic to get approved repos and filter Qdrant search
- `qdrant_client.py`: Added `repo_ids` parameter with should-condition filtering

### Policy Integration
- Both tools use `READ_REPO_REQUIREMENT` policy
- Repo access checks via RepoPolicy
- Node access checks via NodePolicy
- Fail-closed behavior for unknown repos

## Validation

### Acceptance Criteria Met

1. **Context retrieval returns provenance metadata** ✅
   - All provenance fields included in response: file_id, repo_id, node_id, path, relative_path, filename, extension, content_hash, language, indexed_at, score, content_preview

2. **Known-issue records have a structured schema** ✅
   - SQLite storage via IssueRepository with IssueRecord model
   - Qdrant indexing via IssueIndexPayload model
   - Status enum validation (open, in_progress, resolved, wontfix)

3. **Repo access checks still apply** ✅
   - Policy validation via PolicyAwareToolRouter
   - Unknown repo_id returns explicit rejection
   - Filter by repo_id restricts results to approved repos only
   - **SECURITY FIX**: Global search now filters by accessible repos only

### Validation Commands

```bash
ruff check src/hub/tools/context.py src/shared/schemas.py src/hub/dependencies.py src/hub/tool_routing/policy_router.py src/hub/tools/__init__.py src/hub/services/qdrant_client.py
```

All checks pass.

## Integration Points

| Component | Integration Point |
|-----------|------------------|
| QdrantClientWrapper | search_files() for file search, upsert_issue() for issue indexing |
| EmbeddingServiceClient | embed() for query and issue embeddings |
| LLMServicePolicy | get_service("embedding") for embedding service lookup |
| IssueRepository | create() for SQLite issue storage |
| RepoRepository | get() for repo access validation, list_all() for global search access control |
| PolicyAwareToolRouter | Policy validation and dependency injection |

## Notes

- Embedding service must be configured for context search to work
- Qdrant collections must exist from CTX-001/002
- SQLite issues table exists from SETUP-003
- Both tools gracefully handle missing dependencies with appropriate error messages
- Security fix ensures fail-closed behavior for global search access control
