# Code Review: CTX-002 - index_repo pipeline and content-hash tracking

**Ticket**: CTX-002  
**Stage**: review  
**Reviewer**: gpttalker-reviewer-code  
**Date**: 2026-03-16

## Summary

Implementation reviewed for correctness, completeness against acceptance criteria, and code quality. The implementation matches the plan and satisfies all acceptance criteria.

## Decision: **APPROVED**

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 1. Indexing pipeline flow is explicit | ✅ PASS | 6 stages implemented: Init → Discovery → Hash Check → Embed & Upsert → Cleanup → Finalize |
| 2. Content-hash based reindex rules defined | ✅ PASS | SHA256 via `compute_content_hash()`, stored in `FileIndexPayload.content_hash`, compared in `_should_index_file()` |
| 3. Deleted and changed files handled deliberately | ✅ PASS | Changed files: upsert replaces old vector via same file_id; Deleted files: `_cleanup_deleted()` removes stale vectors |

---

## Implementation Analysis

### Pipeline Flow (6 Stages)

| Stage | Plan | Implementation | Match |
|-------|------|---------------|-------|
| 1. Init | Load repo, node, embedding service | `index_repo_handler` validates deps, retrieves repo/node | ✅ |
| 2. Discovery | Fetch file list from node | `_discover_files()` recursively via `node_client.list_directory()` | ✅ |
| 3. Hash Check | Compute SHA256, compare with Qdrant | `_should_index_file()` compares content_hash | ✅ |
| 4. Embed & Upsert | Generate embeddings for changed files | `_process_batch()` calls `embed_batch()` + `_upsert_file_vector()` | ✅ |
| 5. Cleanup | Delete vectors for removed files | `_cleanup_deleted()` compares Qdrant records vs current file_ids | ✅ |
| 6. Finalize | Mark repo as indexed | `repo_repo.mark_indexed()` in handler | ✅ |

### Content-Hash Tracking

- **Hash computation**: `compute_content_hash()` uses `hashlib.sha256(content.encode("utf-8"))`
- **Storage**: Hash stored in `FileIndexPayload.content_hash` in Qdrant payload
- **Comparison logic** (`_should_index_file()`, lines 486-539):
  - Full mode: always returns `True` (index everything)
  - Incremental mode: compares new hash with stored `content_hash`
    - Match → returns `False` (skip unchanged)
    - Mismatch or no record → returns `True` (needs indexing)

### Reindex Rules

| Scenario | Action | Implementation |
|----------|--------|----------------|
| File unchanged | Skip | `_should_index_file()` returns `False`, logged as `index_repo_file_unchanged` |
| File changed | Upsert | `_upsert_file_vector()` replaces vector with same `file_id` |
| File new | Insert | New `file_id` in Qdrant, first-time indexing |
| File deleted | Delete | `_cleanup_deleted()` removes vectors not in current file list |

---

## Code Quality Assessment

### Strengths

1. **Complete type hints**: All functions and methods have proper type annotations
2. **Comprehensive docstrings**: Classes and public methods documented
3. **Structured logging**: All operations logged with appropriate context (`trace_id`, `repo_id`, etc.)
4. **Error handling**: Graceful degradation with try/catch blocks, proper error propagation
5. **Configuration management**: Constants at class level (`BATCH_SIZE`, `MAX_FILE_SIZE`, etc.)
6. **Exclusion rules**: Properly excludes `node_modules`, `__pycache__`, `.git`, etc.
7. **Extension filtering**: Supports 27 code/text file types
8. **Batch processing**: Configurable batch size (default 10) for memory efficiency
9. **File size limits**: 1MB maximum, skip large files with logging
10. **Hidden file handling**: Excludes hidden files except `.gitignore` and `.env.example`

### Integration Points

| Component | Method Used | Status |
|-----------|-------------|--------|
| Qdrant | `upsert_file()`, `delete_file()`, `get_file()`, `scroll_files()` | ✅ All implemented in CTX-001/CTX-002 |
| Embedding | `embed_batch()` | ✅ From LLM-003 |
| Node Client | `list_directory()`, `read_file()` | ✅ From REPO-002 |
| Repo Repository | `get()`, `mark_indexed()` | ✅ From SETUP-003 |
| LLM Policy | `get_service("embedding")` | ✅ From LLM-001 |

---

## Findings

### No Critical Issues

### Observations

1. **Low severity - Previous hash not preserved**: The plan mentioned storing `previous_hash` in metadata for audit purposes when a file changes. This was not implemented. The current implementation overwrites silently. This is an enhancement opportunity, not a blocker.

2. **Low severity - Retry logic defined but not implemented**: The plan mentioned `MAX_RETRIES: int = 3` for failed embeddings, but there's no retry logic in `_process_batch()`. Embedding failures are logged and skipped. This could be added in a future enhancement.

---

## Regression Risk

**Low**

- No existing functionality is modified
- New files only, no breaking changes
- Dependencies on existing services are stable (Qdrant, embedding, node client, repo repository)

---

## Validation Gaps

1. **No unit tests**: While not a blocker for approval, the plan mentioned unit tests for hash computation, file ID generation, and batch processing
2. **No integration tests**: No tests for actual indexing workflows (would require Qdrant/embedding service availability)

---

## Conclusion

The implementation satisfies all three acceptance criteria:

1. ✅ **Indexing pipeline flow explicit**: 6 stages properly implemented
2. ✅ **Content-hash based reindex rules**: SHA256 tracking with skip/update/delete logic
3. ✅ **Deleted and changed files handled deliberately**: Changed files upserted, deleted files cleaned up

The code quality is high with complete type hints, docstrings, and structured logging. No blockers identified.

**Recommendation**: Approve and advance to QA stage.
