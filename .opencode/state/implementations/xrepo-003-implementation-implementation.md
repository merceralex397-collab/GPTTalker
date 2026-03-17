# Implementation: XREPO-003 — Architecture map and project landscape outputs

**Ticket:** XREPO-003  
**Title:** Architecture map and project landscape outputs  
**Wave:** 4  
**Lane:** cross-repo  
**Stage:** implementation  
**Status:** complete

---

## Summary

Implemented the architecture map and project landscape outputs that expose higher-level cross-repo intelligence. This includes:

- Two new MCP tools: `get_architecture_map` and `get_repo_architecture`
- ArchitectureService with language distribution inference from indexed files
- Full integration with existing relationship and owner metadata
- Proper access control bounded to approved repos
- Source citations for all data points (LandscapeSource)

---

## New Files Created

| File | Purpose |
|------|---------|
| `src/hub/services/architecture_service.py` | Core service for architecture map generation |
| `src/hub/tools/architecture.py` | MCP tool handlers |

---

## Modified Files

| File | Modification |
|------|--------------|
| `src/shared/models.py` | Added ArchitectureNode, ArchitectureEdge, ArchitectureMap models; moved RepoOwner before RepoMetadata |
| `src/hub/tools/__init__.py` | Registered `get_architecture_map` and `get_repo_architecture` tools |
| `src/hub/dependencies.py` | Added DI provider for ArchitectureService; passed to PolicyAwareToolRouter |
| `src/hub/tool_routing/policy_router.py` | Added architecture_service parameter to router |

---

## Acceptance Criteria Verification

### 1. Architecture map output shape defined

- **Status:** ✅ Verified
- **Evidence:** `ArchitectureMap` model includes `nodes` (list[ArchitectureNode]), `edges` (list[ArchitectureEdge]), `language_summary` (dict[str, int]), and `landscape_metadata` (LandscapeMetadata). Each ArchitectureNode includes `language_distribution`, `owner`, `file_count`, `issue_count`, and provenance.

### 2. Landscape views cite source repos

- **Status:** ✅ Verified  
- **Evidence:** Every data point includes `LandscapeSource` citation. Sources include repo records (type="repo"), relationship records (type="relationship"), all with citation text.

### 3. Output bounded to approved repos

- **Status:** ✅ Verified
- **Evidence:** All queries filtered through `RepoRepository.list_all()` for access control. Unauthorized repo_ids rejected explicitly. Global view (no repo_ids) returns only accessible repos.

---

## Technical Details

### ArchitectureService Methods

1. **get_architecture_map()** - Generates complete architecture view with:
   - Repository nodes with language distribution (from Qdrant file extensions)
   - Explicit relationships as edges
   - Owner metadata from RepoOwnerRepository
   - Source citations via LandscapeSource
   - Access control via RepoRepository

2. **get_repo_architecture()** - Single repo architecture summary with:
   - Language distribution from indexed files
   - File and issue counts
   - Owner metadata
   - Source citation for the repo

### MCP Tool Parameters

- **get_architecture_map**: `repo_ids`, `include_relationships`, `include_inferred`, `max_depth`
- **get_repo_architecture**: `repo_id`, `include_dependencies`

Both tools use `READ_REPO_REQUIREMENT` policy.

---

## Validation

- All lint checks pass (`ruff check`)
- Format check passes (`ruff format --check`)
- Code follows project standards (type hints, docstrings, structured logging)

---

## Integration Points

| From | Integration |
|------|-------------|
| XREPO-001 | Uses CrossRepoService patterns; extends landscape with architecture |
| XREPO-002 | Uses RelationshipRepository, RepoOwnerRepository |
| CTX-002 | Queries Qdrant for file extensions to infer language distribution |
| CORE-002 | Uses RepoRepository for access control |
