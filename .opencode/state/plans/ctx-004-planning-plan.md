# CTX-004 Implementation Plan: Context bundles and recurring-issue workflows

## Overview

This plan implements higher-order context assembly features that combine existing context data (indexed files, issues) into task-oriented bundles and detect recurring-issue patterns. The implementation builds on the existing CTX-001/002/003 context infrastructure.

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Context bundle output shape is planned | Bundle data model defined with source tracking |
| 2 | Recurring-issue aggregation rules are defined | Aggregation logic implemented with configurable thresholds |
| 3 | Bundle provenance is preserved | Each bundle item tracks source repo, node, file/issue ID, indexed timestamp |

## Context Bundle Approach

### Bundle Types

A **context bundle** is a structured assembly of context data tailored for a specific purpose. This implementation supports three bundle types:

1. **Task Bundle** — Assembled context for a specific task (e.g., "fix bug", "add feature")
   - Contains: relevant files (semantic search results), related issues, recent commits
   - Use case: Provide focused context to an LLM for a specific task

2. **Review Bundle** — Context for code review activities
   - Contains: changed files (git diff context), related issues, recent issues
   - Use case: Pre-flight context before asking for code review

3. **Research Bundle** — Broad exploration context
   - Contains: multiple repo searches, issue summaries, architecture metadata
   - Use case: Understand a codebase or cross-repo relationships

### Bundle Data Model

```python
# New model in src/shared/models.py
class ContextBundlePayload(BaseModel):
    """Payload for a context bundle stored in Qdrant."""
    bundle_id: str
    bundle_type: str  # "task", "review", "research"
    title: str
    description: str | None
    created_at: datetime
    created_by: str  # trace_id of creator
    
    # Bundle composition
    repo_ids: list[str]
    file_ids: list[str]
    issue_ids: list[str]
    
    # Provenance tracking
    sources: list[BundleSource]
    
    # Optional: task metadata
    task_type: str | None
    priority: str | None


class BundleSource(BaseModel):
    """Source tracking for a single item in a bundle."""
    source_type: str  # "file", "issue", "commit"
    source_id: str
    repo_id: str
    node_id: str
    included_at: datetime  # when added to bundle
    relevance_score: float | None
    reason: str | None  # why this was included
```

### Bundle Output Shape

The MCP tool returns:

```python
{
    "success": True,
    "bundle_id": "bundle_abc123",
    "bundle_type": "task",
    "title": "Fix authentication bug",
    "created_at": "2026-03-16T21:00:00Z",
    
    # Composed content
    "files": [
        {
            "file_id": "file_xyz",
            "repo_id": "repo_main",
            "path": "src/auth/login.py",
            "content_preview": "...",
            "relevance_score": 0.95,
            "included_reason": "semantic match for 'authentication flow'"
        }
    ],
    "issues": [
        {
            "issue_id": "issue_123",
            "repo_id": "repo_main", 
            "title": "Login returns 500 on expired token",
            "status": "open",
            "relevance_score": 0.88,
            "included_reason": "semantic match for 'token expiry'"
        }
    ],
    
    # Provenance
    "provenance": {
        "total_sources": 15,
        "repos_included": ["repo_main", "repo_shared"],
        "created_by": "trace_abc",
        "generation_method": "semantic_similarity"
    },
    
    "latency_ms": 450
}
```

## Recurring-Issue Aggregation

### Aggregation Rules

Recurring-issue aggregation detects patterns across issues to help identify:
- Repeated bugs across releases
- Common blockers or dependencies
- Issues that may benefit from combined attention

### Aggregation Methods

1. **Exact Title Match** (default)
   - Issues with identical titles are grouped
   - Threshold: min_count (default: 2)

2. **Semantic Similarity** (optional enhancement)
   - Issues with similar embeddings are grouped
   - Uses Qdrant similarity search over issue collection
   - Threshold: score_threshold (default: 0.85)

3. **Custom Tag Matching**
   - Issues with matching metadata tags
   - Useful for version-related issues (e.g., "v1.2", "v1.3")

### Aggregation Output

```python
{
    "success": True,
    "aggregations": [
        {
            "group_id": "group_auth_001",
            "aggregation_type": "exact_title",
            "representative_title": "Login returns 500 on expired token",
            "count": 3,
            "issues": [
                {
                    "issue_id": "issue_123",
                    "repo_id": "repo_main",
                    "status": "open",
                    "created_at": "2026-01-15",
                    "metadata": {"version": "v1.2"}
                },
                {
                    "issue_id": "issue_456", 
                    "repo_id": "repo_main",
                    "status": "open", 
                    "created_at": "2026-02-20",
                    "metadata": {"version": "v1.3"}
                },
                {
                    "issue_id": "issue_789",
                    "repo_id": "repo_other",
                    "status": "in_progress",
                    "created_at": "2026-03-10",
                    "metadata": {"version": "v1.4"}
                }
            ],
            "first_seen": "2026-01-15",
            "last_seen": "2026-03-10",
            "total_duration_days": 54
        }
    ],
    "summary": {
        "total_groups": 5,
        "total_issues_aggregated": 12,
        "open_issues": 8,
        "resolved_issues": 1,
        "wontfix_issues": 3
    }
}
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| min_count | 2 | Minimum issues to form a recurring group |
| aggregation_type | "exact_title" | Method: "exact_title", "semantic", "tag" |
| score_threshold | 0.85 | For semantic aggregation |
| tag_key | None | For tag-based aggregation |
| status_filter | None | Filter by status: "open", "resolved", etc. |

## Provenance Preservation

### Provenance Tracking Strategy

Every piece of context data included in a bundle or aggregation result carries full provenance:

1. **Source Identification**
   - `source_type`: "file", "issue", "commit"
   - `source_id`: Unique identifier (file_id, issue_id, commit hash)
   - `repo_id`: Repository the source belongs to
   - `node_id`: Node hosting the repo

2. **Temporal Metadata**
   - `indexed_at`: When the source was indexed
   - `included_at`: When the source was added to bundle
   - `bundle_created_at`: Bundle creation timestamp

3. **Relevance Metadata**
   - `relevance_score`: Similarity score from semantic search
   - `included_reason`: Natural language explanation for inclusion

4. **Causality Tracking**
   - `created_by`: trace_id of the request that created the bundle
   - `generation_method`: How the bundle was assembled (e.g., "semantic_similarity", "manual")

### Provenance Storage

- Bundles stored in Qdrant `gpttalker_summaries` collection with `bundle_id` as point ID
- Aggregation results computed on-demand (not stored, to keep fresh)
- Bundle access logged in task history for audit

## New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/tools/bundles.py` | Context bundle MCP tool handlers (build_context_bundle) |
| `src/hub/tools/recurring.py` | Recurring-issue aggregation handler (list_recurring_issues) |
| `src/hub/services/bundle_service.py` | Bundle assembly logic and provenance tracking |
| `src/hub/services/aggregation_service.py` | Issue aggregation logic |

## Existing Files to Modify

| File | Changes |
|------|---------|
| `src/shared/models.py` | Add `ContextBundlePayload`, `BundleSource` models |
| `src/hub/services/qdrant_client.py` | Add bundle upsert/search methods to COLLECTION_SUMMARIES |
| `src/hub/tools/__init__.py` | Register `build_context_bundle` and `list_recurring_issues` tools |
| `src/hub/dependencies.py` | Add DI providers for bundle and aggregation services |

## Implementation Steps

### Step 1: Add Models (src/shared/models.py)
- Add `ContextBundlePayload` model with bundle composition and provenance fields
- Add `BundleSource` model for source tracking
- Add `RecurringIssueGroup` model for aggregation results

### Step 2: Extend Qdrant Client (src/hub/services/qdrant_client.py)
- Add `upsert_bundle()` method to store bundles in COLLECTION_SUMMARIES
- Add `search_bundles()` method for bundle retrieval
- Add `scroll_bundles()` method for listing bundles

### Step 3: Create Bundle Service (src/hub/services/bundle_service.py)
- Implement `build_task_bundle()` - assembles files + issues for a task
- Implement `build_review_bundle()` - assembles change context
- Implement `build_research_bundle()` - assembles exploration context
- Implement provenance tracking in each build method

### Step 4: Create Aggregation Service (src/hub/services/aggregation_service.py)
- Implement `aggregate_by_title()` - exact title matching
- Implement `aggregate_by_similarity()` - semantic clustering (optional enhancement)
- Implement `aggregate_by_tag()` - metadata tag grouping

### Step 5: Create Tool Handlers

**bundles.py**:
- `BuildContextBundleParams` - parameters for bundle creation
- `build_context_bundle_handler()` - main MCP tool handler

**recurring.py**:
- `ListRecurringIssuesParams` - parameters for aggregation
- `list_recurring_issues_handler()` - main MCP tool handler

### Step 6: Register Tools (src/hub/tools/__init__.py)
- Register `build_context_bundle` tool with `READ_REPO_REQUIREMENT` policy
- Register `list_recurring_issues` tool with `READ_REPO_REQUIREMENT` policy

### Step 7: Add DI Providers (src/hub/dependencies.py)
- Add `get_bundle_service()` provider
- Add `get_aggregation_service()` provider

## Integration Points

| Component | Integration |
|-----------|------------|
| Qdrant Client | Reuse existing `search_files`, `search_issues` for content assembly |
| IssueRepository | Reuse `list_recurring()` for basic aggregation, enhance with Qdrant |
| EmbeddingService | Generate query embeddings for bundle assembly |
| RepoRepository | Validate repo access for bundle contents |
| Policy Engine | Apply READ_REPO_REQUIREMENT to bundle items |

## Validation Plan

1. **Unit Tests**
   - Test bundle model serialization
   - Test aggregation logic (exact title, semantic)
   - Test provenance tracking

2. **Integration Tests**
   - Test bundle creation end-to-end
   - Test recurring aggregation with real Qdrant
   - Test policy enforcement on bundle items

3. **Manual Verification**
   - Create a task bundle and verify all sources have provenance
   - Run recurring aggregation and verify group accuracy
   - Verify bundle can be retrieved by ID

## Risks and Assumptions

| Risk | Mitigation |
|------|------------|
| Semantic aggregation is expensive | Make it optional, default to exact title matching |
| Large bundles exceed response limits | Add `max_items` parameter with reasonable default (50) |
| Provenance storage grows large | Bundles are small metadata; files/issues are referenced, not duplicated |

## Blockers

None. All required infrastructure (Qdrant, issue repository, embedding service) exists from CTX-001/002/003.

## Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Bundle storage | Qdrant COLLECTION_SUMMARIES | Already exists, supports semantic search |
| Aggregation default | Exact title matching | Simple, reliable, no additional API calls |
| Bundle type | Task, Review, Research | Covers main use cases from canonical brief |
| Provenance format | Structured BundleSource model | Enables audit and traceability |
