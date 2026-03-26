# EXEC-008 Plan Review

## Ticket
- **ID:** EXEC-008
- **Title:** Close remaining hub path and write-target security edge cases
- **Wave:** 10
- **Lane:** security
- **Stage:** plan_review

---

## Decision: APPROVED

---

## Review of Alleged Blocker: `test_unregistered_write_target_denied`

### The Planner's Claim
The planning artifact declares `test_unregistered_write_target_denied` (test_security.py:213) **OUT OF SCOPE**, citing the brief constraint that says "The fix preserves base-boundary, symlink, and extension-allowlist enforcement." The planner interpreted this as prohibiting any test changes, claiming the test mocks `.get` but the code calls `.get_by_path` — and concluded this requires either a prohibited test change or a code change that would break real functionality.

### The Evidence

**Code reality** (`src/hub/policy/write_target_policy.py:38`):
```python
target = await self._repo.get_by_path(path)
```

**Test reality** (`tests/hub/test_security.py:207-208`):
```python
mock_repo = MagicMock()
mock_repo.get = AsyncMock(return_value=None)  # ← wrong method!
```

The test mocks `.get()` but the real code calls `.get_by_path()`. When the code `await`s the result of `.get_by_path()`, it gets a non-awaitable `MagicMock` object and raises:
```
TypeError: object MagicMock can't be used in 'await' expression
```

### The Acceptance Criteria Explicitly Names This Issue

EXEC-008 acceptance criterion 3 states:
> "`WriteTargetPolicy` rejects unknown targets through its async repository contract **without depending on non-awaitable mocks**."

This language was deliberately inserted into the acceptance criteria. It directly acknowledges that the mock issue exists and that fixing it is part of EXEC-008's scope. The phrase "without depending on non-awaitable mocks" is a constraint on the test's mock configuration — the test must be corrected to use the right async method.

### Why the Constraint Does Not Apply Here

The brief says: "The fix preserves base-boundary, symlink, and extension-allowlist enforcement."

This constraint governs **code security behavior** — it means: don't change the security checks in the actual implementation. It does **not** mean: preserve broken test infrastructure. The distinction is:

| What the constraint protects | What it does NOT protect |
|---|---|
| Path boundary checks in `normalize()` | Broken test mocks that mock the wrong method |
| Symlink escape rejection | Tests that configure `get` instead of `get_by_path` |
| Extension allowlist enforcement | Mock configuration that causes `TypeError` |

### Correct Classification

The defect in `test_unregistered_write_target_denied` is a **pre-existing broken test mock**, not a code defect. Fixing it is:

1. **One line**: Change `mock_repo.get = AsyncMock(...)` → `mock_repo.get_by_path = AsyncMock(...)`
2. **Zero behavioral change**: The test still exercises the same fail-closed logic — unregistered path → `ValueError`
3. **Explicitly in scope**: Acceptance criterion 3 names this exact problem

---

## Review of the Other 4 Fixes

All 4 remaining fixes are sound:

### Fix 1: `test_path_traversal_dotdot_rejected` — APPROVED
- **Root cause:** Error message lacks the word "traversal"
- **Fix:** Change error message at `path_utils.py:93` to include "traversal"
- **Verdict:** Correct, low-risk string change

### Fix 2: `test_home_directory_expansion_rejected` — APPROVED
- **Root cause:** `~` is validated AFTER `.resolve()` expands it away
- **Fix:** Add `~` rejection BEFORE `.resolve()` in `normalize()`
- **Verdict:** Correct — adds a needed security check before path resolution

### Fix 3: `test_invalid_path_rejected` — APPROVED
- **Root cause:** `validate_no_traversal()` called on pre-normalized path, misses `.` components
- **Fix:** Reorder to call `normalize()` before `validate_no_traversal()` in `read_repo_file_handler()`
- **Verdict:** Correct — validates the normalized (resolved) path

### Fix 4: `test_write_markdown_validates_extension` — APPROVED  
- **Root cause:** Test function missing `mock_write_target` fixture parameter
- **Fix:** Add `mock_write_target` to function parameters
- **Verdict:** Correct — explicitly allowed test change per brief

---

## Files to Modify

| File | Change | Risk |
|------|--------|------|
| `src/hub/policy/path_utils.py` | Fix error message (line 93), add `~` rejection before resolve | Low |
| `src/hub/tools/inspection.py` | Reorder `normalize()` / `validate_no_traversal()` (lines 251-262) | Low |
| `tests/hub/test_security.py` | Fix `test_unregistered_write_target_denied`: `mock_repo.get` → `mock_repo.get_by_path` | Low |
| `tests/hub/test_contracts.py` | Add `mock_write_target` to `test_write_markdown_validates_extension` parameters | Low |

---

## Validation

After applying all 5 fixes:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no
```
Should exit 0 with all tests passing.

---

## Conclusion

The alleged blocker is **INVALID**. The broken mock in `test_unregistered_write_target_denied` is a pre-existing defect that was either introduced when `WriteTargetPolicy` was refactored to use `get_by_path`, or always present and never caught. The acceptance criteria explicitly calls out "non-awaitable mocks" — meaning the code is correct and the test mock needs fixing. The brief constraint about preserving "base-boundary, symlink, and extension-allowlist enforcement" governs code behavior only, not test infrastructure.

**Plan is decision-complete. Proceed to implementation.**
