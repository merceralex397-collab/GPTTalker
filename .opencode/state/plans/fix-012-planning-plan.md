# Implementation Plan: FIX-012 - Complete Cross-Repo Landscape with Real Metrics

## 1. Scope

Replace hardcoded zeros and empty values in `cross_repo_service.py` with real queries:
- `file_count`: Query actual indexed file count from Qdrant
- `issue_count`: Query actual issue count from IssueRepository
- `languages`: Detect languages from indexed file extensions
- Relationship finder: **Already implemented** (lines 277-315 use content hash overlap)

## 2. Files or Systems Affected

| File | Change Type | Description |
|------|-------------|-------------|
| `src/shared/repositories/issues.py` | Modify | Add `count_by_repo()` method (or use existing `list_by_repo()` + len) |
| `src/hub/services/qdrant_client.py` | Modify | Add `count_files_by_repo()` and `get_unique_languages()` methods |
| `src/hub/services/cross_repo_service.py` | Modify | Replace hardcoded values with real queries, add IssueRepository |
| `src/hub/dependencies.py` | Modify | Pass IssueRepository to CrossRepoService via DI |

## 3. Implementation Steps

### Step 1: Add `count_by_repo()` to IssueRepository

Add a new method to `src/shared/repositories/issues.py`:

```python
async def count_by_repo(self, repo_id: str) -> int:
    """Get count of issues for a specific repository."""
    row = await self._db.fetchone(
        "SELECT COUNT(*) as count FROM issues WHERE repo_id = ?",
        (repo_id,),
    )
    return row["count"] if row else 0
```

### Step 2: Add Qdrant methods

Add to `src/hub/services/qdrant_client.py`:
- `count_files_by_repo(repo_id)` - count indexed files for a repo using Qdrant count API
- `get_unique_languages(repo_id)` - detect languages from indexed file extensions

### Step 3: Update CrossRepoService constructor

Update `__init__` to accept `issue_repo` parameter:
```python
def __init__(
    self,
    ...,
    issue_repo: "IssueRepository | None" = None,
) -> None:
    self.issue_repo = issue_repo
```

### Step 4: Replace hardcoded values in `get_project_landscape()`

Replace hardcoded values in `src/hub/services/cross_repo_service.py`:
- `file_count`: Use `qdrant_client.count_files_by_repo()`
- `issue_count`: Use `issue_repo.count_by_repo()`
- `languages`: Use `qdrant_client.get_unique_languages()`

### Step 5: Update `search_across_repos()` file counts

Replace hardcoded file counts with real queries using the same methods.

### Step 6: Update dependencies.py

Add `issue_repo: IssueRepository` parameter to `get_cross_repo_service()`:
```python
async def get_cross_repo_service(
    ...
    issue_repo: IssueRepository = Depends(get_issue_repository),  # Add this
) -> "CrossRepoService":
    return CrossRepoService(
        ...,
        issue_repo=issue_repo,
    )
```

## 4. Acceptance Criteria

| Criterion | Verification Method |
|-----------|---------------------|
| file_count reflects actual indexed file count from Qdrant | Query Qdrant for indexed files count |
| issue_count reflects actual issue count from IssueRepository | Query SQLite issues table |
| languages are detected from indexed file extensions | Check language field in Qdrant payloads |
| Relationship finder uses content hash overlap | Already implemented (lines 277-315) |

## 5. Validation

- Run `python3 -m py_compile` on all modified files
- Run `python3 -c "from src.hub.services.cross_repo_service import CrossRepoService"`
- All queries wrapped in try/except with graceful fallback

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Qdrant count API may be slow | Use efficient count API, fallback to 0 |
| Empty repos should return 0 | All queries wrapped in try/except |

## 7. Blocker Checklist

- [x] No blocking decisions remain
- [x] All required methods exist or are being added
- [x] Relationship finder is already implemented (no change needed)