# Implementation of XREPO-001: Cross-repo search and global context query

## Summary

Implemented cross-repo search and global context query functionality that enables searching across multiple indexed repositories, finding related repos, and generating project landscape views.

## Files Created

### 1. `src/hub/services/cross_repo_service.py` (419 lines)
Service layer providing cross-repo operations:
- **search_across_repos**: Semantic search across multiple repos with access control
- **list_related_repos**: Find related repos based on shared content (files/issues/bundles)
- **get_project_landscape**: Overview of all accessible repos with metadata

### 2. `src/hub/tools/cross_repo.py` (329 lines)
MCP tool handlers:
- **search_across_repos_handler**: Cross-repo semantic search
- **list_related_repos_handler**: Related repo discovery
- **get_project_landscape_handler**: Project overview generation

## Files Modified

### 1. `src/shared/models.py`
Added new models:
- `RepoMetadata`: Metadata summary for a repo in cross-repo results
- `FileSearchHit`: Individual file hit from cross-repo search
- `CrossRepoSearchResult`: Aggregated search result from cross-repo search
- `RelatedRepo`: A repository related to another via shared content
- `ProjectLandscape`: Overview of all accessible repositories

### 2. `src/hub/tools/__init__.py`
Registered 3 new MCP tools:
- `search_across_repos`: Semantic search across repos
- `list_related_repos`: Find related repositories
- `get_project_landscape`: Get project overview

### 3. `src/hub/dependencies.py`
Added DI provider:
- `get_cross_repo_service`: Dependency injection for CrossRepoService

## Acceptance Criteria Verification

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| Cross-repo query path is defined | ✅ | `search_across_repos` tool with semantic search across multiple repos |
| Per-repo access controls still apply | ✅ | Uses `RepoRepository.list_all()` to get accessible repos, rejects unknown repo_ids |
| Returned results keep repo-level provenance | ✅ | Each file result includes `repo_id`, `node_id`, `path`, `filename`, `extension`, `language`, `score` |

## Key Implementation Details

### Access Control
- All operations use `RepoRepository.list_all()` to get accessible repos
- Unknown/inaccessible repo_ids are rejected with fail-closed behavior
- Global search (no repo_ids) filters results to accessible repos only

### Provenance Tracking
- Each file result includes full provenance: `repo_id`, `node_id`, `path`, `relative_path`, `filename`, `extension`, `language`, `score`, `content_preview`
- Repo metadata includes `repo_id`, `node_id`, `file_count`, `issue_count`, `last_indexed_at`, `languages`

### Performance Considerations
- Search limited to max 20 repos for performance
- Result limit enforced (max 100)
- Score threshold filtering available

## Validation

- Ruff lint check: ✅ All checks passed
- Code follows existing patterns from context.py, bundles.py, and recurring.py
- Uses existing QdrantClientWrapper and EmbeddingServiceClient

## Integration Points

| Point | Dependency | Interface |
|-------|------------|-----------|
| Qdrant search | CTX-001 | `QdrantClientWrapper.search_files(repo_ids=...)` |
| Repo access control | CORE-002 | `RepoRepository.list_all()` |
| Embedding generation | LLM-003 | `EmbeddingServiceClient.embed()` |
| Tool registration | SETUP-004 | `ToolRegistry.register()` |
| Policy requirements | CORE-005/006 | `READ_REPO_REQUIREMENT` |
