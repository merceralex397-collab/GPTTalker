# EXEC-013 Planning Artifact

## Ticket
- **ID**: EXEC-013
- **Title**: Fix datetime.UTC, collections.abc, and TimeoutError alias violations
- **Wave**: 11
- **Lane**: bugfix
- **Stage**: planning

## Problem Statement
Ruff reports alias-modernization violations (UP017, UP035, UP041) in three files:
- `src/hub/services/node_health.py` — UP017 (datetime.UTC alias)
- `tests/conftest.py` — UP035 (collections.abc) and UP041 (TimeoutError)
- `src/hub/services/tunnel_manager.py` — UP035 (collections.abc) and UP041 (TimeoutError)

All violations are mechanical alias replacements with no functional changes.

---

## File-by-File Changes

### 1. `src/hub/services/node_health.py` — UP017

**Violations:** `datetime.now(timezone.utc)` should use `datetime.UTC` alias.

**Changes:**
- Line 3: Change `from datetime import datetime, timezone` → `from datetime import UTC, datetime`
- Line 73: Change `datetime.now(timezone.utc)` → `datetime.now(UTC)`
- Line 149: Change `datetime.now(timezone.utc)` → `datetime.now(UTC)`
- Line 175: Change `datetime.now(timezone.utc)` → `datetime.now(UTC)`

**Import line (after):**
```python
from datetime import UTC, datetime
```

---

### 2. `tests/conftest.py` — UP035

**Violations:** `typing.AsyncGenerator` and `typing.Generator` should be imported from `collections.abc`.

**Changes:**
- Line 6: Change `from typing import AsyncGenerator, Generator` → `from collections.abc import AsyncGenerator, Generator`

**Import line (after):**
```python
from collections.abc import AsyncGenerator, Generator
```

---

### 3. `src/hub/services/tunnel_manager.py` — UP035 and UP041

**Violations:**
- `asyncio.TimeoutError` should be replaced with builtin `TimeoutError` (UP041)

**Changes:**
- The file currently catches `asyncio.TimeoutError` on line 376. No import change needed — `TimeoutError` is a builtin.
- Change `except asyncio.TimeoutError:` → `except TimeoutError:` on line 376.

Note: The file does not appear to use `typing.AsyncGenerator` or `typing.Generator` directly, so UP035 may not actually apply here. The acceptance criterion targets the three files for verification; if Ruff finds no UP035 issues in tunnel_manager.py, no change is needed for that rule in this file.

---

## Validation Plan

Run the acceptance criterion command:
```
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/services/node_health.py tests/conftest.py src/hub/services/tunnel_manager.py
```

Expected exit code: 0 (all violations resolved).

---

## Scope Boundary

This plan covers **EXEC-013 only**. The following are explicitly out of scope for this ticket:
- Import ordering (I001, I002)
- Unused imports (F401)
- Unused variables (F841)
- Mechanical issues (F541, B008, C401, C414)
- datetime.utcnow() in other files (UP038) — handled by EXEC-014
- Any changes to `src/shared/repositories/*.py`, `src/shared/models.py`, or other files

EXEC-014 is the dependent follow-up ticket for remaining mechanical violations.

---

## Risks and Assumptions

- **Assumption:** All changes are pure alias replacements with identical runtime semantics.
- **Assumption:** No other files in the scope of criterion 1 have additional violations beyond the identified ones.
- **Risk:** If `asyncio.TimeoutError` is caught in multiple places in tunnel_manager.py beyond line 376, those also need updating. (Inspection shows only one catch site.)
- **Risk:** Ruff may surface additional UP035 issues in tunnel_manager.py (e.g., other typing aliases). These would be addressed by updating the import as needed; the acceptance criterion requires exit 0.
