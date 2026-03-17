# QA Verification: CTX-002 - index_repo pipeline and content-hash tracking

**Ticket**: CTX-002  
**Stage**: qa  
**Date**: 2026-03-16  
**Decision**: **PASSED**

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 1. Indexing pipeline flow is explicit | ✅ PASS | 6 stages implemented in `indexing_pipeline.py` |
| 2. Content-hash based reindex rules defined | ✅ PASS | SHA256 tracking with skip/update/delete logic |
| 3. Deleted and changed files handled deliberately | ✅ PASS | Changed upserted, deleted cleaned up |

---

## Detailed Analysis

### 1. Pipeline Flow (6 Stages)

| Stage | Plan | Implementation | Location |
|-------|------|---------------|----------|
| 1. Init | Load repo, node, embedding service | Handler validates deps, retrieves repo/node | `indexing.py:60-85` |
| 2. Discovery | Fetch file list from node | `_discover_files()` recursively | `indexing_pipeline.py:258-355` |
| 3. Hash Check | Compute SHA256, compare with Qdrant | `_should_index_file()` | `indexing_pipeline.py:486-539` |
| 4. Embed & Upsert | Generate embeddings for changed files | `_process_batch()` + `_upsert_file_vector()` | `indexing_pipeline.py:385-600` |
| 5. Cleanup | Delete vectors for removed files | `_cleanup_deleted()` | `indexing_pipeline.py:602-643` |
| 6. Finalize | Mark repo as indexed | `repo_repo.mark_indexed()` | `indexing.py:109` |

### 2. Content-Hash Tracking

- **Hash computation**: `compute_content_hash()` uses `hashlib.sha256(content.encode("utf-8"))` (models.py:260-271)
- **Storage**: Hash stored in `FileIndexPayload.content_hash` (indexing_pipeline.py:573)
- **Comparison logic** (`_should_index_file()` at lines 518-527):
  - Full mode: always returns `True`
  - Incremental mode: compares new hash with stored `content_hash`
    - Match → returns `False` (skip unchanged)
    - Mismatch or no record → returns `True` (needs indexing)

### 3. Reindex Rules

| Scenario | Action | Implementation |
|----------|--------|----------------|
| File unchanged | Skip | `_should_index_file()` returns `False`, logged as `index_repo_file_unchanged` |
| File changed | Upsert | `_upsert_file_vector()` replaces vector with same `file_id` |
| File new | Insert | New `file_id` in Qdrant |
| File deleted | Delete | `_cleanup_deleted()` removes vectors not in current file list |

---

## Code Quality

- **Type hints**: Complete on all functions/methods
- **Docstrings**: All classes and public methods documented
- **Structured logging**: All operations logged with appropriate context
- **Error handling**: Graceful degradation with try/catch blocks

---

## Validation Commands

```bash
# Lint check
ruff check src/hub/services/indexing_pipeline.py src/hub/tools/indexing.py

# Type check  
mypy src/hub/services/indexing_pipeline.py src/hub/tools/indexing.py
```

---

## Conclusion

All 3 acceptance criteria are satisfied. The implementation correctly implements:
1. A 6-stage explicit pipeline flow
2. SHA256 content-hash tracking for idempotent reindexing
3. Deliberate handling of deleted and changed files

**Decision: PASSED - Ready for closeout**
