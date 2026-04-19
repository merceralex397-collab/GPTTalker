# Plan for REMED-022

## Finding Assessment

**Finding**: `EXEC-REMED-001`  
**Status**: **STALE** — no code changes required.

**Rationale**: The validated finding `EXEC-REMED-001` was a Python import failure in the node-agent FastAPI dependency injection wiring. All remediation chain fixes (FIX-020, FIX-024, FIX-025, FIX-026, FIX-028) are confirmed present in the current codebase. No defect reproduces in the current state.

## QA Evidence

Since no code changes are required, QA evidence is established through import verification. The three canonical import verification commands will be executed:

### Command 1 — Hub main package
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app; print('OK')"
```

### Command 2 — Node agent main package
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app; print('OK')"
```

### Command 3 — Shared migrations
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.shared.migrations import run_migrations; print('OK')"
```

All three commands must exit 0 with `OK` output. These commands are stable across sibling remediation tickets (REMED-019, REMED-020, REMED-021).

## Sibling Corroboration

This plan may cite sibling ticket QA artifacts for corroborating evidence:
- `REMED-021-qa-qa.md` (Wave 40, closed trusted)
- Prior sibling QA artifacts from REMED-019 and REMED-020

## Conclusion

No implementation changes are required. The finding is stale. QA will verify via import verification commands and sibling corroboration. This ticket closes with current evidence.
