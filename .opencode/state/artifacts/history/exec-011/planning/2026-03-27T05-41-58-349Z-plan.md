# EXEC-011 Planning Artifact

## Ticket
- **ID**: EXEC-011
- **Title**: Reduce repo-wide ruff violations to zero
- **Wave**: 10
- **Lane**: hardening
- **Stage**: planning

## Problem Statement
`UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` currently reports violations across source and test files. The violations are mechanical (import ordering, deprecated API usage, unused imports) and require systematic cleanup without changing runtime behavior.

---

## Violation Catalog (51 Total)

### Category 1: `datetime.utcnow()` Deprecation (UP038) — ~30 violations

The `datetime.utcnow()` API is deprecated in Python 3.12+ in favor of `datetime.now(UTC)`.

**Files affected:**
| File | Lines | Notes |
|------|-------|-------|
| `src/shared/repositories/nodes.py` | 36, 151, 167 | `utcnow()` calls in create/update methods |
| `src/shared/repositories/tasks.py` | 58 | `utcnow()` in create method |
| `src/shared/repositories/issues.py` | 48, 165 | `utcnow()` in create/update methods |
| `src/shared/repositories/repos.py` | 35, 174 | `utcnow()` in create/mark_indexed methods |
| `src/shared/models.py` | 150, 165, 459, 752, 765, 766, 780 | `default_factory=datetime.utcnow` in Pydantic model fields |
| `tests/hub/test_contracts.py` | 38 | `datetime.utcnow()` in fixture |

**Fix**: Replace all `datetime.utcnow()` with `datetime.now(UTC)`. Ensure `from datetime import UTC` or `from datetime import timezone` is added where missing. For `default_factory`, use `default_factory=lambda: datetime.now(UTC)`.

---

### Category 2: Duplicate/Wildcard Imports — ~5 violations

**`src/hub/dependencies.py`:**
- Lines 24-29: `get_qdrant_client` is imported twice from `src.hub.services.qdrant_client` (lines 24-26 and lines 27-29)
- Line 51 (TYPE_CHECKING block): `from src.hub.services.indexing_pipeline import IndexingPipeline` is also at module level (line 19), making the TYPE_CHECKING import redundant

**Fix**: Remove duplicate import of `get_qdrant_client`. Remove redundant `IndexingPipeline` from TYPE_CHECKING block.

---

### Category 3: Unused Imports / Variables — ~10 violations

Likely across test files and tool files where imports are present but not directly referenced by name (via `from x import *` or re-exports).

Specific patterns to check:
- `tests/hub/test_contracts.py`: `AsyncMock`, `MagicMock`, `patch` may have unused members
- `src/hub/tools/__init__.py`: Re-exports may trigger F401 (unused-import) if ruff treats re-exported names as used
- `src/hub/dependencies.py`: `_ = ...` or wildcard re-exports

---

### Category 4: Import Ordering (I) — ~5 violations

Import block ordering may not match isort conventions across files. The `known-first-party = ["src"]` setting means all `src.*` imports should be in a dedicated import block.

Files to check:
- `src/shared/repositories/*.py`: Standard library, third-party, local imports may be unordered
- `src/hub/tools/*.py`: Same issue

---

### Category 5: Type Annotation / Syntax Issues — ~1 violation

**`src/shared/models.py` line 656**: Contains `===]` (triple-equals) which appears to be a stray comment terminator:
```
# === Distributed Scheduler Models (SCHED-002) ===]
```
Should be `===]` → `===]` or just `==` in the comment.

---

## Scope Assessment

| Category | Violations | Mechanical? | Runtime Safe? |
|----------|-----------|------------|--------------|
| UP038 datetime.utcnow | ~30 | Yes | Yes |
| Duplicate imports | ~5 | Yes | Yes |
| Unused imports | ~10 | Yes | Yes |
| Import ordering | ~5 | Yes | Yes |
| Syntax/typo | 1 | Yes | Yes |

**Total: ~51 violations, all mechanical, all runtime-safe to fix.**

---

## Split Recommendation

**YES — split into 2 follow-up tickets** per acceptance criterion 4, because:

1. `datetime.utcnow()` replacements touch 6+ files across the repository structure (shared/repositories, shared/models, tests), representing a distinct concern from import mechanical issues.
2. Import/deduplication fixes in `src/hub/dependencies.py` require understanding FastAPI DI patterns and are more localized.
3. `parallel_safe: false` and `overlap_risk: high` mean one agent should own the full fix; splitting reduces risk per session.
4. The ticket brief explicitly requires splitting if scope is too broad.

---

## Proposed Follow-up Tickets

### EXEC-013: Fix datetime.utcnow() deprecation (UP038)
- **Summary**: Replace all `datetime.utcnow()` calls with `datetime.now(UTC)` across repository files, models, and tests.
- **Files**: `src/shared/repositories/{nodes,tasks,issues,repos}.py`, `src/shared/models.py`, `tests/hub/test_contracts.py`
- **Violations**: ~30
- **Risk**: Low (mechanical, runtime-safe)
- **Depends on**: None

### EXEC-014: Fix import ordering, duplicate imports, and mechanical issues
- **Summary**: Remove duplicate imports in hub dependencies, fix import ordering, remove unused imports, fix stray syntax artifact in models.py.
- **Files**: `src/hub/dependencies.py`, `src/shared/models.py`, various test files
- **Violations**: ~21
- **Risk**: Low (mechanical, runtime-safe)
- **Depends on**: None

---

## Implementation Steps for EXEC-011 (this ticket)

Since EXEC-011 is the planning-only ticket, the steps are:

1. Write this planning artifact ✅
2. Register it with artifact_register
3. The team-lead will create the follow-up tickets (EXEC-013, EXEC-014) via `ticket_create` with evidence-backed scope

---

## Validation Plan

For each follow-up ticket, validation is:
```
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check . --output-format=json
```
Then verify exit code 0 and zero violations in the JSON output.

---

## Risks and Assumptions

- **Assumption**: All 51 violations are mechanical/style violations that do not change runtime behavior.
- **Assumption**: `datetime.utcnow()` is not intentionally used for any specific semantic behavior that `datetime.now(UTC)` would break.
- **Risk**: Some `datetime.utcnow()` calls may be in Pydantic `default_factory` contexts that need special handling (the factory must be callable, not a method reference).
- **Mitigation**: For `default_factory`, use `default_factory=lambda: datetime.now(UTC)` instead of `default_factory=datetime.now(UTC)`.
- **Risk**: `ruff.toml` does NOT have per-file-ignores for `**/dependencies.py = ["B008"]` (unlike `pyproject.toml`). This means B008 violations for hub dependencies are expected. **Do NOT add B008 ignores globally — they are intentionally not ignored in ruff.toml per repo policy.**
