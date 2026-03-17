# Planning: XREPO-003 — Architecture map and project landscape outputs

**Ticket:** XREPO-003  
**Title:** Architecture map and project landscape outputs  
**Wave:** 4  
**Lane:** cross-repo  
**Stage:** planning  
**Status:** in_progress  
**Depends on:** XREPO-001, XREPO-002

---

## 1. Scope

This ticket implements higher-order cross-repo intelligence by exposing architecture and landscape outputs that combine:

- Repository structure and language distribution
- Explicit and inferred relationships (from XREPO-002)
- Owner and maintainer metadata (from XREPO-002)
- Source citations for all data points

The work builds directly on XREPO-001 (cross-repo search) and XREPO-002 (relationships and owner metadata).

---

## 2. Files or Systems Affected

### New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/services/architecture_service.py` | Core service for architecture map generation |
| `src/hub/tools/architecture.py` | MCP tool handlers for architecture endpoints |
| `src/shared/models.py` | Add `ArchitectureMap`, `ArchitectureNode`, `ArchitectureEdge` models |

### Files to Modify

| File | Modification |
|------|--------------|
| `src/hub/tools/__init__.py` | Register `get_architecture_map` and `get_repo_architecture` tools |
| `src/hub/dependencies.py` | Add DI provider for `ArchitectureService` |
| `src/shared/models.py` | Add new architecture models (if not in new file) |

---

## 3. Implementation Steps

### Step 1: Define Architecture Data Models

Add Pydantic models for architecture representation:

```python
# Architecture node representing a single repo in the architecture view
class ArchitectureNode(BaseModel):
    repo_id: str
    node_id: str
    name: str
    language_distribution: dict[str, int]  # language -> file count
    file_count: int
    issue_count: int
    owner: RepoOwner | None = None
    category: str | None = None  # inferred or explicit (frontend, backend, etc.)

# Architecture edge representing relationships between repos
class ArchitectureEdge(BaseModel):
    source_repo_id: str
    target_repo_id: str
    relationship_type: RelationshipType
    confidence: float
    description: str | None = None

# Complete architecture map
class ArchitectureMap(BaseModel):
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]
    total_repos: int
    total_files: int
    language_summary: dict[str, int]  # aggregated language distribution
    landscape_metadata: LandscapeMetadata  # includes sources and ownership
```

### Step 2: Implement ArchitectureService

Create `ArchitectureService` in `src/hub/services/architecture_service.py`:

- `get_architecture_map(repo_ids: list[str] | None, include_relationships: bool)` — Generates full architecture view
- `get_repo_architecture(repo_id: str)` — Returns single-repo architecture summary
- Internal helper: `_infer_language_distribution(repo_id)` — Queries Qdrant for file extensions
- Internal helper: `_build_edges(relationships, inferred)` — Combines explicit + inferred relationships
- Access control: All queries filtered through `RepoRepository` for approved repos only

### Step 3: Implement MCP Tool Handlers

Add handlers in `src/hub/tools/architecture.py`:

```python
class GetArchitectureMapParams(BaseModel):
    repo_ids: list[str] | None  # None = all accessible
    include_relationships: bool = True
    include_inferred: bool = True  # inferred from file overlap
    max_depth: int = 3  # for dependency traversal

class GetRepoArchitectureParams(BaseModel):
    repo_id: str
    include_dependencies: bool = False
```

### Step 4: Register Tools

Add to `src/hub/tools/__init__.py`:

- `get_architecture_map` — Returns architecture map with language distribution, relationships, source citations
- `get_repo_architecture` — Returns single-repo architecture summary with owner and relationship context

Both tools use `READ_REPO_REQUIREMENT` policy.

### Step 5: Add DI Provider

Add `get_architecture_service` provider in `src/hub/dependencies.py`:

```python
async def get_architecture_service(
    qdrant_client: QdrantClientWrapper,
    repo_repo: RepoRepository,
    relationship_repo: RelationshipRepository | None,
    owner_repo: RepoOwnerRepository | None,
) -> ArchitectureService:
    return ArchitectureService(
        qdrant_client=qdrant_client,
        repo_repo=repo_repo,
        relationship_repo=relationship_repo,
        owner_repo=owner_repo,
    )
```

---

## 4. Validation Plan

### Unit Tests

- `test_architecture_node_model` — Validates model serialization
- `test_architecture_service_access_control` — Ensures only approved repos returned
- `test_language_distribution_inference` — Tests Qdrant query for extensions

### Integration Tests

- `test_get_architecture_map_returns_citations` — Verifies `LandscapeSource` citations present
- `test_get_architecture_map_filters_by_access` — Ensures unauthorized repos excluded
- `test_get_repo_architecture_single_repo` — Validates single-repo output shape

### Validation Commands

```bash
# Run tests
pytest tests/hub/services/test_architecture_service.py -v
pytest tests/hub/tools/test_architecture.py -v

# Lint
ruff check src/hub/services/architecture_service.py src/hub/tools/architecture.py
```

---

## 5. Risks and Assumptions

| Risk | Mitigation |
|------|------------|
| Language inference may be slow for large repos | Limit to indexed files in Qdrant; cache results |
| Circular relationships in dependency graphs | Use max_depth parameter; detect cycles |
| Missing owner metadata for some repos | Allow None; landscape view still functional |

**Assumptions:**

- Qdrant file index includes `extension` and `language` fields (from CTX-002)
- RelationshipRepository and RepoOwnerRepository available via DI (from XREPO-002)
- RepoRepository provides access control filtering (from CORE-002)

---

## 6. Acceptance Criteria

1. **Architecture map output shape defined**  
   - Output includes `nodes` (list of ArchitectureNode), `edges` (list of ArchitectureEdge), `language_summary`, and `landscape_metadata`
   - Each node includes `language_distribution`, `owner`, and provenance

2. **Landscape views cite source repos and metadata**  
   - Every data point includes `LandscapeSource` citation
   - Sources include: repo, relationship, owner records

3. **Output bounded to approved repos**  
   - All queries filtered through `RepoRepository.list_all()` 
   - Unauthorized repo_ids rejected explicitly
   - Global view (no repo_ids) returns only accessible repos

---

## 7. Integration Points

| From | Integration |
|------|-------------|
| XREPO-001 | Uses `CrossRepoService` for relationship data; extends landscape with architecture |
| XREPO-002 | Uses `RelationshipRepository`, `RepoOwnerRepository` for explicit relationships and owners |
| CTX-002 | Queries Qdrant for file extensions to infer language distribution |
| CORE-002 | Uses `RepoRepository` for access control |

---

## 8. Decision Blockers

None. All required infrastructure exists from prior tickets.
