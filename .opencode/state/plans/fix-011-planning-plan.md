# Implementation Plan for FIX-011: Complete Aggregation Service Methods

## 1. Current Stub Analysis

The current stub implementations in `src/hub/services/aggregation_service.py` have the following issues:

### `aggregate_by_title` (lines 32-77)
- Calls `scroll_bundles(bundle_type="issue")` but doesn't use the result
- Logs parameters but performs no aggregation
- Returns empty aggregations with placeholder note
- **Problem**: No actual grouping logic implemented

### `aggregate_by_similarity` (lines 79-125)
- Only logs parameters
- Returns empty aggregations with placeholder note
- **Problem**: No semantic similarity search implemented

### `aggregate_by_tag` (lines 127-168)
- Only logs parameters
- Returns empty aggregations with placeholder note
- **Problem**: No tag-based grouping logic implemented

---

## 2. Implementation Specification

### 2.1 Dependencies Required

The `AggregationService` needs access to `IssueRepository` for SQLite-backed issue data. This requires:

1. Adding `IssueRepository` as a constructor dependency
2. Using it to fetch issues for aggregation operations

### 2.2 `aggregate_by_title` Implementation

**Approach**: Use `IssueRepository.list_recurring(min_count)` which already implements exact title matching via SQL GROUP BY.

**Algorithm**:
1. Call `issue_repo.list_recurring(min_count)` to get titles with counts >= min_count
2. For each title group, fetch all issues with that exact title from the repository
3. Build `RecurringIssueGroup` objects with:
   - group_id: hash of title
   - aggregation_type: "exact_title"
   - representative_title: the grouped title
   - count: number of issues
   - issue_ids: list of issue IDs
   - repo_ids: unique repo IDs from the group
   - first_seen/last_seen: temporal bounds
4. Apply status_filter if provided (filter groups where any issue matches)
5. Return aggregated results with `AggregationSummary`

### 2.3 `aggregate_by_similarity` Implementation

**Approach**: Use Qdrant semantic search to find similar issues.

**Algorithm**:
1. Scroll a sample of issues from Qdrant (using `scroll_bundles(bundle_type="issue")` or query issues collection)
2. For each anchor issue, generate embedding from title+description
3. Search for similar issues using `search_issues()` with score_threshold
4. Group issues that are mutually similar (if A is similar to B and B is similar to A, group them)
5. Filter groups with count >= min_count
6. Apply repo_ids filter if provided
7. Return aggregated results

**Note**: Full implementation requires issue embeddings to exist in Qdrant. The service should handle the case where no embeddings exist by falling back to a simpler approach or returning appropriate warning.

### 2.4 `aggregate_by_tag` Implementation

**Approach**: Query IssueRepository and group by metadata tag values.

**Algorithm**:
1. Fetch all issues from IssueRepository (optionally filtered by repo_ids)
2. For each issue, check if `metadata` contains the specified `tag_key`
3. Group issues by their tag value (issues with the same tag value go together)
4. Filter groups where count >= min_count
5. Build `RecurringIssueGroup` objects similar to title aggregation
6. Return aggregated results

---

## 3. File Changes Required

### 3.1 Modify: `src/hub/services/aggregation_service.py`

**Changes**:
1. Add `IssueRepository` import
2. Update constructor to accept `issue_repo: IssueRepository` parameter
3. Implement `aggregate_by_title()` with real logic
4. Implement `aggregate_by_similarity()` with Qdrant-based semantic clustering
5. Implement `aggregate_by_tag()` with metadata-based grouping
6. Remove all placeholder comments and "note" fields

### 3.2 Modify: `src/hub/dependencies.py` (if needed)

**Check**: Verify that `AggregationService` is provided via DI and update if constructor signature changes.

---

## 4. Implementation Steps

### Step 1: Update AggregationService Constructor
```python
def __init__(
    self,
    qdrant_client: QdrantClientWrapper,
    issue_repo: IssueRepository,  # Add this
) -> None:
    self.qdrant_client = qdrant_client
    self.issue_repo = issue_repo  # Store reference
```

### Step 2: Implement `aggregate_by_title`
1. Call `self.issue_repo.list_recurring(min_count)` 
2. For each result, fetch full issue details via `self.issue_repo.list_by_repo()` or iterate and filter
3. Build groups and compute summary statistics
4. Return structured response

### Step 3: Implement `aggregate_by_similarity`
1. Sample issues from Qdrant or SQLite as anchor points
2. For each anchor, generate/query embedding
3. Search for similar issues using Qdrant
4. Cluster similar issues into groups
5. Return structured response

### Step 4: Implement `aggregate_by_tag`
1. Fetch all issues (optionally filtered by repo_ids)
2. Extract tag values from metadata dict
3. Group by tag value
4. Filter by min_count
5. Return structured response

### Step 5: Update DI Provider
- Ensure `AggregationService` receives `IssueRepository` in dependencies.py

---

## 5. Validation Steps

### 5.1 Code Quality
- [ ] Run `ruff check src/hub/services/aggregation_service.py` - no errors
- [ ] Run `python3 -m py_compile src/hub/services/aggregation_service.py` - succeeds
- [ ] All type hints present and correct

### 5.2 Functional Validation
- [ ] `aggregate_by_title` returns non-empty results when duplicate titles exist
- [ ] `aggregate_by_similarity` returns results when Qdrant has issue embeddings
- [ ] `aggregate_by_tag` returns grouped results when issues have metadata tags
- [ ] All filters (repo_ids, min_count, status_filter) work correctly

### 5.3 Edge Cases
- [ ] Empty database returns appropriate empty response (not error)
- [ ] Non-existent tag_key returns empty aggregations
- [ ] min_count filtering works correctly
- [ ] repo_ids filtering restricts results appropriately

---

## 6. Acceptance Criteria Verification

| Criterion | Verification Method |
|-----------|---------------------|
| aggregate_by_title groups issues by exact title match from IssueRepository | Call method with issues having duplicate titles, verify groups formed |
| aggregate_by_similarity uses Qdrant semantic search to cluster related issues | Create issues with embeddings, verify semantic clustering works |
| aggregate_by_tag groups issues by metadata tag keys | Add issues with metadata tags, verify grouping by tag value |
| No placeholder comments or empty aggregation returns remain | Code review: no "note" fields, no "requires integration" comments |

---

## 7. Risks and Assumptions

### Assumptions
- IssueRepository is available and functional (it exists from SETUP-003)
- Qdrant issues collection has or can have embeddings for semantic search
- Issues have metadata field that can store tag values

### Risks
- **Semantic similarity** requires issue embeddings to exist in Qdrant - if not, the method may return empty results
- **Tag aggregation** depends on metadata being populated on issues - if empty, returns no groups

### Mitigation
- Add graceful handling when Qdrant has no embeddings (return empty with clear message)
- Document requirement for metadata tags in issue creation

---

## 8. Blocker Checklist

- [ ] No blocking decisions remain
- [ ] All required dependencies (IssueRepository) are already implemented
- [ ] Qdrant client methods (search_issues, scroll_bundles) are available
- [ ] Model classes (RecurringIssueGroup, AggregationSummary) are defined
