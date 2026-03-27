# EXEC-014 Planning Artifact

## Ticket
- **ID**: EXEC-014
- **Title**: Fix remaining mechanical Ruff violations after EXEC-013
- **Wave**: 11
- **Lane**: hardening
- **Stage**: planning
- **Depends on**: EXEC-013

## Summary

Clear the remaining mechanical Ruff violations from the 2026-03-27 lint report. All violations are cosmetic/mechanical — no functional changes.

## Configuration Clarification

**B008 handling**: `pyproject.toml` (which ruff uses when both `ruff.toml` and `pyproject.toml` exist) contains:
```toml
[tool.ruff]
ignore = ["E501", "B008"]  # B008 globally ignored
[tool.ruff.per-file-ignores]
"**/dependencies.py" = ["B008"]  # redundant but harmless
```

This means:
- B008 is **globally ignored** for ALL files including `src/hub/dependencies.py`
- The `per-file-ignores` for `**/dependencies.py = ["B008"]` is **redundant but harmless**
- All existing `# noqa: B008` comments in `src/hub/dependencies.py` are **redundant**
- The implementer should remove the redundant `# noqa: B008` comments as part of this cleanup

**ruv.toml vs pyproject.toml**: When both exist, ruff uses `pyproject.toml`. The `ruff.toml` at the project root is not used by ruff in this configuration.

---

## Known Violations (from prior evidence and static analysis)

### 1. `tests/conftest.py` — 2 violations

| Rule | Line | Issue | Fix |
|------|------|-------|-----|
| I001 | 6 | `from collections.abc import ...` is before `from pathlib import Path` — alphabetically `collections` (c) > `pathlib` (p), so `collections.abc` should come AFTER `pathlib` | Reorder: move `collections.abc` line after `pathlib` line |
| F401 | 3 | `import os` is unused | Delete the `import os` line |

**Note from EXEC-013 implementation**: These are pre-existing issues confirmed NOT introduced by EXEC-013.

### 2. `src/hub/dependencies.py` — 3+ violations

| Rule | Lines | Issue | Fix |
|------|-------|-------|-----|
| I001 / E402 | 919 | `from src.hub.policy.distributed_scheduler import DistributedScheduler` is placed at the bottom of the file after all function definitions. All other `src.hub.policy` imports are at lines 11-16. | Move the import to the top of the file with the other `src.hub.policy` imports (lines 11-16) |
| I001 | 24-29 | Two separate import blocks from the same module `src.hub.services.qdrant_client` — `QdrantClientWrapper` on lines 24-26 and `get_qdrant_client as get_qdrant` on lines 27-29 | Consolidate into ONE import block |
| F401 | (likely) | Multiple `# noqa: B008` comments that are redundant since B008 is globally ignored | Remove all `# noqa: B008` comments |

**E402 analysis for line 919**: When a Python file has imports AFTER function definitions (not inside a function), this triggers E402 ("module level import not at top of file"). Moving `DistributedScheduler` to the top with the other `src.hub.policy` imports is the correct fix. The original placement was likely to avoid circular imports — but moving it to the top alongside other policy imports (which already work) should be safe.

### 3. `src/shared/models.py` — potential syntax artifact

| Line | Issue | Status |
|------|-------|--------|
| 656 | `# === Distributed Scheduler Models (SCHED-002) ===]` — the `===]` ending is unusual but in a comment | No ruff violation expected since it's a comment. Verify with `ruff check src/shared/models.py --select S` or similar if ruff reports it |

---

## Auto-fixable Violations

The following should be handled by `ruff check --fix` before manual fixes:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check . --fix
```

Expected auto-fixable categories:
- **F401** (unused imports) — auto-remove unused imports
- **F841** (unused variables) — auto-rename to `_` or remove
- **I001** (import order) — auto-reorder in most cases
- **C401** (unnecessary generator) — `list(x for x in y)` → `list(y)`
- **C414** (redundant comprehension) — `list(list(x) for x in y)` → `[list(x) for x in y]`
- **F541** (f-string without placeholders) — convert to regular string
- **B007** (useless statement) — auto-remove

---

## File-by-File Change List

### `tests/conftest.py`

**Change 1 — Fix I001 import order**:
```
# BEFORE (lines 3-7):
import os
import sys
from pathlib import Path
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

# AFTER:
import sys
from pathlib import Path
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock
```

**Change 2 — Remove F401 unused `os` import**:
Delete line 3 (`import os`).

### `src/hub/dependencies.py`

**Change 1 — Consolidate duplicate qdrant_client imports (lines 24-29)**:
```
# BEFORE (lines 24-29):
from src.hub.services.qdrant_client import (
    QdrantClientWrapper,
)
from src.hub.services.qdrant_client import (
    get_qdrant_client as get_qdrant,
)

# AFTER (lines 24-27):
from src.hub.services.qdrant_client import (
    QdrantClientWrapper,
    get_qdrant_client as get_qdrant,
)
```

**Change 2 — Move DistributedScheduler import to top (line 919 → near line 16)**:
Move `from src.hub.policy.distributed_scheduler import DistributedScheduler` from line 919 to be with the other `src.hub.policy` imports at lines 11-16.

**Change 3 — Remove redundant `# noqa: B008` comments**:
Remove all `# noqa: B008` comments from all `Depends()` calls in the file. Since B008 is globally ignored in pyproject.toml, these are redundant.

### `src/shared/models.py`

No changes planned for line 656 (`===]` in comment) unless ruff reports a violation. Verify with:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/shared/models.py
```

---

## B008 Handling Guidance

**When to suppress B008**: NEVER add new `# noqa: B008` comments. The global ignore in pyproject.toml covers all FastAPI `Depends()` patterns.

**When to remove B008 suppression**: Remove all existing `# noqa: B008` comments in `src/hub/dependencies.py` since they are redundant (B008 is globally ignored).

**Files with B008 in FastAPI dependency patterns**: `src/hub/dependencies.py` — all `Depends()` calls are intentional FastAPI DI patterns, not actual B008 violations. The noqa comments exist because B008 was previously not globally ignored, but now that it is, they should be removed.

---

## Implementation Steps

### Step 1: Run auto-fix
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check . --fix
```

### Step 2: Verify and address remaining issues

After auto-fix, run:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```

Address any remaining violations manually:

**A. If I001 remains in tests/conftest.py**: Manually reorder imports (auto-fix may not handle the specific `collections.abc` vs `pathlib` ordering correctly)

**B. If E402 remains in src/hub/dependencies.py**: Confirm DistributedScheduler import is at the top with other policy imports

**C. If F401 (unused os) remains in tests/conftest.py**: Manually delete `import os`

**D. Consolidate QdrantClient imports in src/hub/dependencies.py** if auto-fix didn't merge them

**E. Remove all `# noqa: B008` comments in src/hub/dependencies.py**

### Step 3: Final verification
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```
Must exit 0.

---

## Validation Plan

**Acceptance criterion**: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` exits 0

**Step 1 — Pre-fix snapshot**:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check . --output-format=json > /tmp/ruff_before.json 2>&1 || true
wc -l /tmp/ruff_before.json
```

**Step 2 — Apply fixes**:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check . --fix
# Then manually fix remaining issues in:
# - tests/conftest.py (import order, unused os)
# - src/hub/dependencies.py (consolidate imports, move DistributedScheduler, remove noqa B008)
```

**Step 3 — Final check**:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```
Must exit 0 with zero violations.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Auto-fix introduces unwanted changes | Review diff after `--fix` before committing |
| Moving DistributedScheduler import causes circular import | If circular import occurs, keep import at bottom but add `# noqa: E402` to suppress the E402 warning (E402 is acceptable for intentional late imports to avoid cycles) |
| Removing `# noqa: B008` uncovers real B008 issues | B008 is globally ignored in pyproject.toml — no real B008 issues should exist |
| Import reordering in tests/conftest.py breaks pytest fixtures | The import order doesn't affect runtime; pytest will still work |

---

## Dependencies and Prerequisites

- **Prerequisite**: EXEC-013 must be fully landed and verified (`ruff check --select UP017,UP035,UP041` exits 0)
- **Scope boundary**: This ticket covers F541, E402, B008, F841, C401, C414, I001, F401, B007 only. UP017/UP035/UP041 are handled by EXEC-013.

---

## Outcome

After this ticket lands:
- `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` exits 0
- All mechanical Ruff violations are resolved
- No functional code changes
- B008 FastAPI dependency patterns remain properly handled (via global ignore, not noqa comments)
