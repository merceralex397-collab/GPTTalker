# Code Review: CTX-003 - get_project_context and known-issue records

**Ticket**: CTX-003  
**Title**: get_project_context and known-issue records  
**Review Stage**: Code Review  
**Decision**: NEEDS_FIXES

---

## Summary

Implementation is largely complete with all acceptance criteria addressed, but there is a **Medium severity security issue** with repo access control that requires fixing before approval.

---

## Findings

### ✅ Finding 1: Provenance Metadata Complete (No Action Required)

**Severity**: N/A  
**Status**: PASS

The `get_project_context_handler` returns comprehensive provenance metadata in each result:

| Field | Source | Present |
|-------|--------|---------|
| file_id | Qdrant payload | ✅ |
| repo_id | Qdrant payload | ✅ |
| node_id | Qdrant payload | ✅ |
| path | Qdrant payload | ✅ |
| relative_path | Qdrant payload | ✅ |
| filename | Qdrant payload | ✅ |
| extension | Qdrant payload | ✅ |
| language | Qdrant payload | ✅ |
| content_hash | Qdrant payload | ✅ |
| size_bytes | Qdrant payload | ✅ |
| line_count | Qdrant payload | ✅ |
| indexed_at | Qdrant payload | ✅ |
| score | Qdrant search | ✅ |
| content_preview | Qdrant payload | ✅ |

---

### ✅ Finding 2: Issue Schema Structured (No Action Required)

**Severity**: N/A  
**Status**: PASS

The `record_issue_handler` implements proper structured issue management:

- **SQLite Storage**: Uses `IssueRepository.create()` with IssueRecord model
- **Qdrant Indexing**: Uses `IssueIndexPayload` for semantic search
- **Status Validation**: Validates against IssueStatus enum (open, in_progress, resolved, wontfix)
- **Graceful Degradation**: Issue created in SQLite even if Qdrant indexing fails

---

### ⚠️ Finding 3: Repo Access Control Bypass in Global Search

**Severity**: Medium  
**Status**: REQUIRES FIX

**Issue**: When `get_project_context` is called without a `repo_id` filter (global search), the Qdrant query returns results from **ALL indexed repos** regardless of user access permissions.

**Root Cause**:
1. `PolicyAwareToolRouter._validate_policy()` only validates repo access if `repo_id` is present in parameters
2. When `repo_id=None`, policy validation skips repo check (line 244-249 in policy_router.py)
3. `QdrantClientWrapper.search_files()` applies no repo filter when `repo_id=None` (line 318-319 in qdrant_client.py)
4. Handler also skips validation when `repo_id` is None (lines 77-85 in context.py)

**Impact**: A user with access to Node A (containing Repo X) but NOT Node B (containing Repo Y) can still see Repo Y content through global search.

**Acceptance Criteria Violated**: "Repo access checks still apply to retrieved context"

**Recommended Fix** (choose one):

**Option A** (Recommended - Defense in Depth):
```python
# In get_project_context_handler, when repo_id is None:
# Fetch all accessible repos and filter results in-memory

if not params.repo_id and repo_repo:
    # Get all approved repos for this user
    all_repos = await repo_repo.list()
    approved_repo_ids = {r.repo_id for r in all_repos}
    
    # Filter search results to only approved repos
    results = [
        r for r in results 
        if r.get("repo_id") in approved_repo_ids
    ]
```

**Option B** (Simpler - Enforce repo_id):
Make `repo_id` required for `get_project_context`, breaking global search but ensuring access control.

---

### ✅ Finding 4: Policy Registration Correct

**Severity**: N/A  
**Status**: PASS

Both tools are correctly registered with `READ_REPO_REQUIREMENT` policy:
- `get_project_context` → line 415 in __init__.py
- `record_issue` → line 457 in __init__.py

---

### ✅ Finding 5: DI Integration Complete

**Severity**: N/A  
**Status**: PASS

Dependencies properly injected via PolicyAwareToolRouter:
- `qdrant_client` → lines 441-445 in policy_router.py
- `embedding_client` → lines 446-450 in policy_router.py
- `issue_repo` → lines 451-455 in policy_router.py
- `repo_repo` → lines 401-405 in policy_router.py

---

## Code Quality Observations

### Low Severity: Handler Duplicate Validation
The handler performs manual repo validation (lines 77-85, 209-220) that mirrors policy validation. This is defense-in-depth but redundant. Not a blocker.

### Low Severity: Status Enum Import
The handler imports `IssueStatus` from `src.shared.models` (line 13) for validation but the actual creation uses string conversion. Could be more explicit. Not a blocker.

---

## Regression Risks

1. **None identified** - Implementation follows existing patterns from CTX-001/002

---

## Test Gaps

1. **Missing**: Unit test for global search with multiple accessible repos
2. **Missing**: Integration test for repo access bypass scenario
3. **Missing**: Test verifying results filtered when repo_id=None

---

## Validation Commands (Not Executable - Bash Restricted)

```bash
# Type check
python -m py_compile src/hub/tools/context.py src/shared/schemas.py

# Import check  
python -c "from src.hub.tools.context import get_project_context_handler, record_issue_handler"
```

---

## Decision

**NEEDS_FIXES** - Medium severity security issue must be addressed before approval.

The implementation is otherwise complete and well-structured. Once the repo access control bypass is fixed, this ticket can be approved.
