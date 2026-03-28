# EXEC-011 Implementation: Reduce repo-wide ruff violations to zero

## Overview

EXEC-011 was opened to resolve all mechanical Ruff violations in the GPTTalker repo. After initial analysis, the work was split into two narrower follow-up tickets (EXEC-013 and EXEC-014) because the scope was too broad for a single lane.

This document records the execution of both child tickets and the final outcome.

## Execution Split

| Child Ticket | Scope | Status |
|---|---|---|
| EXEC-013 | UP017 (datetime.UTC), UP035 (collections.abc), UP041 (asyncio.TimeoutError) alias violations in 3 specific files | Done + Trusted |
| EXEC-014 | All remaining violations: F541, E402, B008, F841, C401, C414, I001, F401, B007 across the full repo | Done + Trusted |

## EXEC-013 Execution (closed 2026-03-27)

**Scope:** 3 specific files — `src/hub/services/node_health.py`, `tests/conftest.py`, `src/hub/services/tunnel_manager.py`

**Fixes applied:**
- `datetime.now(timezone.utc)` → `datetime.UTC` (UP017) in node_health.py
- `typing.AsyncGenerator`/`typing.Generator` → `collections.abc.AsyncGenerator`/`collections.abc.Generator` (UP035)
- `asyncio.TimeoutError` → builtin `TimeoutError` (UP041)

**Artifacts:**
- Plan: `.opencode/state/artifacts/history/exec-013/planning/2026-03-27T07-04-26-225Z-plan.md`
- Implementation: `.opencode/state/artifacts/history/exec-013/implementation/2026-03-27T07-12-38-634Z-implementation.md`
- Review: `.opencode/state/artifacts/history/exec-013/review/2026-03-27T07-15-28-802Z-review.md`
- QA: `.opencode/state/artifacts/history/exec-013/qa/2026-03-27T07-18-18-033Z-qa.md`
- Smoke-test: `.opencode/state/artifacts/history/exec-013/smoke-test/2026-03-27T07-22-41-396Z-smoke-test.md` — PASS

## EXEC-014 Execution (closed 2026-03-27)

**Scope:** All remaining violations across the full repo.

### Phase 1 — Initial plan-only fix (insufficient)

First implementation attempt only addressed the two files mentioned in the original plan (`tests/conftest.py` and `src/hub/dependencies.py`). This left ~125 violations across ~30 files unaddressed because:

1. The plan was **decision-incomplete**: it didn't account for the repo-wide scope of violations
2. `ruff.toml` overrides `pyproject.toml` for Ruff configuration — the original plan assumed B008 was globally ignored via pyproject.toml, but ruff.toml did not include B008 in its ignore list

First smoke-test: FAILED (exit 1)

### Phase 2 — Blocker identification and full remediation

**Root cause:** `ruff.toml` contains `ignore = ["E501"]` while `pyproject.toml` contains `ignore = ["E501", "B008"]`. When both files exist, Ruff reads `ruff.toml` and B008 violations were being reported globally.

**Fix applied to `ruff.toml`:**
```toml
[lint]
ignore = ["E501", "B008"]
```

**Post-fix `ruff check --fix` across the full repo:**
- Auto-fixed violations in ~26 files (F401 unused imports, F541 f-string without placeholder, etc.)
- Manual fixes required in 6 remaining files:
  - `src/hub/services/aggregation_service.py`: F841 (unused variable), C401×3 (unnecessary `list()`/`dict()`/set())
  - `src/hub/services/qdrant_client.py`: C414 (unnecessary `sorted()`)
  - `src/hub/services/relationship_service.py`: B007 (unused loop variable)
  - `tests/conftest.py`: import order (I001), unused `os` import (F401)
  - `src/hub/dependencies.py`: redundant noqa B008 comments removed

**Second smoke-test: PASS** (exit 0)

### Final violation counts after full remediation

All violations resolved:
- B008: ignored globally via ruff.toml
- I001/F401: resolved in conftest.py and dependencies.py
- F541: auto-fixed across repo
- F841: manually fixed in aggregation_service.py
- C401×3: manually fixed in aggregation_service.py
- C414: manually fixed in qdrant_client.py
- B007: manually fixed in relationship_service.py

## Final Acceptance

`UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` exits **0**.

Both child tickets (EXEC-013, EXEC-014) are closed with `verification_state: trusted`.

EXEC-011 parent ticket tracked the repo-wide lint-zero objective. The objective is now achieved through the split execution of EXEC-013 and EXEC-014.
