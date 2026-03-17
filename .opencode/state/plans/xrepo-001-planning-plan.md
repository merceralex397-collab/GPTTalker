# Implementation Plan: XREPO-001 - Cross-repo search and global context query

## 1. Scope

Implement global context and search flows that aggregate approved results across multiple indexed repositories. This ticket builds on the existing CTX-001/002/003 context infrastructure to expose higher-level cross-repo discovery tools.

### Existing Infrastructure (CTX-001/002/003)

| Component | Location | Purpose |
|-----------|----------|---------|
| QdrantClientWrapper | `src/hub/services/qdrant_client.py` | Vector search across files, issues, bundles |
| get_project_context | `src/hub/tools/context.py` | Semantic search with optional repo_id filter |
| build_context_bundle | `src/hub/tools/bundles.py` | Cross-repo context aggregation |
| list_recurring_issues | `src/hub/tools/recurring.py` | Cross-repo issue aggregation |
| RepoRepository | `src/shared/repositories/repos.py` | Repo registry and access control |

### Gap Analysis

The existing `get_project_context` tool supports global search (no `repo_id`) but:
- Returns file results only, not aggregated metadata per repo
- Does not expose repo relationship/landscape views
- Lacks a dedicated "search across repos" MCP tool with explicit multi-repo semantics

---

## 2. Files or Systems Affected

### New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/tools/cross_repo.py` | New MCP tool handlers for cross-repo search |
| `src/hub/services/cross_repo_service.py` | Service layer for cross-repo query logic |

### Existing Files to Modify

| File | Modification |
|------|--------------|
| `src/hub/tools/__init__.py` | Register new cross-repo tools |
| `src/shared/models.py` | Add CrossRepoSearchResult, RepoMetadata models |
| `src/hub/dependencies.py` | Add DI provider for CrossRepoService (optional) |

---

## 3. Implementation Steps

### Step 1: Define Data Models

Add new Pydantic models to `src/shared/models.py`:

```python
class RepoMetadata(BaseModel):
    """Metadata summary for a single repo in cross-repo results."""
    repo_id: str
    node_id: str
    file_count: int
    issue_count: int
    last_indexed_at: datetime | None
    languages: list[str]


class CrossRepoSearchResult(BaseModel):
    """Aggregated search result from cross-repo search."""
    query: str
    total_results: int
    repos_searched: int
    repo_metadata: list[RepoMetadata]
    file_results: list[FileSearchHit]
    latency_ms: int


class FileSearchHit(BaseModel):
    """Individual file hit from cross-repo search."""
    file_id: str
    repo_id: str
    node_id: str
    path: str
    filename: str
    extension: str
    language: str | None
    score: float
    content_preview: str | None
```

### Step 2: Create CrossRepoService

Create `src/hub/services/cross_repo_service.py` with:

1. **search_across_repos(query, repo_ids, limit, score_threshold)**
   - Get accessible repos from RepoRepository (access control)
   - Generate query embedding via EmbeddingServiceClient
   - Search Qdrant gpttalker_files collection with repo_ids filter
   - Aggregate results and compute per-repo metadata
   - Return results with full provenance

2. **list_related_repos(repo_id)**
   - Find repos that share similar files, issues, or bundles
   - Use Qdrant to find repos with overlapping file content embeddings
   - Return list of related repo IDs with relationship metadata

3. **get_project_landscape()**
   - Get all accessible repos
   - For each repo, get file count, issue count, languages from Qdrant
   - Return aggregated landscape view with repo relationships

### Step 3: Create MCP Tool Handlers

Create `src/hub/tools/cross_repo.py`:

1. **search_across_repos_handler**
   - Parameters: `query`, `repo_ids` (optional), `limit`, `score_threshold`
   - Returns: CrossRepoSearchResult with file hits and repo metadata
   - Policy: READ_REPO_REQUIREMENT (validates each repo_id)

2. **list_related_repos_handler**
   - Parameters: `repo_id`, `relationship_type` (files/issues/bundles), `limit`
   - Returns: List of related repos with relationship metadata
   - Policy: READ_REPO_REQUIREMENT

3. **get_project_landscape_handler**
   - Parameters: `include_relationships` (bool)
   - Returns: Landscape view with all accessible repos and their metadata
   - Policy: READ_REPO_REQUIREMENT (access control via RepoRepository)

### Step 4: Register Tools

Add to `src/hub/tools/__init__.py`:

```python
def register_cross_repo_tools(registry: ToolRegistry) -> None:
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.cross_repo import (
        search_across_repos_handler,
        list_related_repos_handler,
        get_project_landscape_handler,
    )

    # search_across_repos
    registry.register(ToolDefinition(
        name="search_across_repos",
        description="Search indexed content across multiple repositories. "
        "Performs semantic search over files in specified repos or all accessible repos. "
        "Returns results with per-repo metadata and full provenance.",
        handler=search_across_repos_handler,
        parameters={...},
        policy=READ_REPO_REQUIREMENT,
    ))

    # list_related_repos
    registry.register(ToolDefinition(
        name="list_related_repos",
        description="Find repositories related to a given repo based on shared content, "
        "issues, or bundles.",
        handler=list_related_repos_handler,
        parameters={...},
        policy=READ_REPO_REQUIREMENT,
    ))

    # get_project_landscape
    registry.register(ToolDefinition(
        name="get_project_landscape",
        description="Get an overview of all accessible repositories with their metadata. "
        "Includes file counts, issue counts, languages, and optional relationship data.",
        handler=get_project_landscape_handler,
        parameters={...},
        policy=READ_REPO_REQUIREMENT,
    ))
```

Update `register_all_tools()` to call `register_cross_repo_tools(registry)`.

### Step 5: Add DI Provider (Optional)

Add to `src/hub/dependencies.py`:

```python
async def get_cross_repo_service(...) -> CrossRepoService:
    return CrossRepoService(
        qdrant_client=qdrant_client,
        embedding_client=embedding_client,
        llm_service_policy=llm_service_policy,
        repo_repo=repo_repo,
    )
```

---

## 4. Validation Plan

### Unit Tests

| Test | Coverage |
|------|----------|
| CrossRepoService.search_across_repos | Returns results with correct provenance |
| CrossRepoService.search_across_repos | Filters to accessible repos only |
| CrossRepoService.list_related_repos | Returns related repos |
| CrossRepoService.get_project_landscape | Returns all accessible repos |
| Tool handlers | Return structured MCP responses |

### Integration Tests

| Test | Coverage |
|------|----------|
| search_across_repos | Returns files from multiple repos with repo_id in each hit |
| search_across_repos | Rejects unknown repo_ids (fail-closed) |
| list_related_repos | Returns repos with overlapping content |
| get_project_landscape | Returns metadata for all accessible repos |

### Validation Commands

```bash
# Lint
ruff check src/hub/tools/cross_repo.py src/hub/services/cross_repo_service.py

# Type check
python -m mypy src/hub/tools/cross_repo.py src/hub/services/cross_repo_service.py

# Tests (if written)
pytest tests/hub/tools/test_cross_repo.py -v
```

---

## 5. Risks and Assumptions

### Risks

| Risk | Mitigation |
|------|------------|
| Large number of repos causes slow search | Limit `repo_ids` to max 20, add latency tracking |
| Memory usage with many results | Enforce `limit` parameter (max 100) |
| Qdrant query complexity | Use existing `search_files` which has proper filtering |

### Assumptions

| Assumption | Validation |
|------------|------------|
| CTX-002 index_repo has populated gpttalker_files | Precondition: At least one repo must be indexed |
| Embedding service is configured | Precondition: LLM service registry has EMBEDDING type |
| RepoRepository is accessible | Precondition: SETUP-003 completed |

---

## 6. Blockers or Required User Decisions

### Decision Blockers

None. All architectural decisions are aligned with existing patterns:

- **Access control**: Reuse `RepoRepository.list_all()` pattern from get_project_context
- **Search**: Reuse `QdrantClientWrapper.search_files()` with `repo_ids` parameter
- **Provenance**: Include `repo_id`, `node_id` in each result (matching existing FileIndexPayload)
- **Error handling**: Use same pattern as existing tools (return dict with success/error)

### Required Preconditions

| Precondition | Met By |
|--------------|--------|
| Qdrant collections exist | CTX-001 |
| At least one repo indexed | CTX-002 |
| Embedding service configured | LLM-003 |
| Repo registry populated | CORE-002 |

---

## 7. Acceptance Criteria Summary

| # | Criterion | Implementation |
|---|-----------|----------------|
| 1 | Cross-repo query path is defined | `search_across_repos` tool with semantic search across multiple repos |
| 2 | Per-repo access controls still apply | Uses `RepoRepository.list_all()` to get accessible repos, rejects unknown repo_ids |
| 3 | Returned results keep repo-level provenance | Each file result includes `repo_id`, `node_id`, `path`; repo metadata included |

---

## 8. Integration Points

| Point | Dependency | Interface |
|-------|------------|-----------|
| Qdrant search | CTX-001 | `QdrantClientWrapper.search_files(repo_ids=...)` |
| Repo access control | CORE-002 | `RepoRepository.list_all()` |
| Embedding generation | LLM-003 | `EmbeddingServiceClient.embed()` |
| Tool registration | SETUP-004 | `ToolRegistry.register()` |
| Policy requirements | CORE-005/006 | `READ_REPO_REQUIREMENT` |

---

## 9. File Manifest

### New Files

```
src/hub/services/cross_repo_service.py  # Service layer (150-200 lines)
src/hub/tools/cross_repo.py             # MCP tool handlers (150-200 lines)
```

### Modified Files

```
src/shared/models.py                     # Add 3 new model classes (~40 lines)
src/hub/tools/__init__.py               # Register 3 new tools (~50 lines)
src/hub/dependencies.py                  # Add DI provider (~20 lines, optional)
```

### Total Estimated Lines

- New: ~350-400 lines
- Modified: ~60-70 lines
