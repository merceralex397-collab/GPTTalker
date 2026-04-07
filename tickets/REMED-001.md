# REMED-001: Hub service cannot start — RelationshipService TYPE_CHECKING runtime annotation

## Summary

`src/hub/dependencies.py` uses `RelationshipService` (imported under `TYPE_CHECKING`) as a
runtime return-type annotation on `get_relationship_service()`. This causes a `NameError` at
module load and prevents the hub from starting.

Fix: Change `-> RelationshipService:` to `-> "RelationshipService":` (string annotation) on
line 835 of `src/hub/dependencies.py`. Similar patterns may exist elsewhere in `src/`.

## Wave

12

## Lane

remediation

## Parallel Safety

- parallel_safe: false
- overlap_risk: low

## Stage

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- finding_source: EXEC001
- source_ticket_id: None
- source_mode: net_new_scope

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `uv run python -c "from src.hub.main import app"` exits 0
- [ ] `uv run python -c "from src.node_agent.main import app"` exits 0
- [ ] `uv run python -c "from src.shared"` exits 0
- [ ] Run `ruff check .` and `uv run pytest tests/ --collect-only -q --tb=no` with zero errors

## Artifacts

- None yet

## Notes

Root cause: `RelationshipService` guard-imported under `TYPE_CHECKING` block
(`src/hub/dependencies.py` lines 47-53) but referenced as a runtime annotation on line 835.
Use `-> "RelationshipService":` (PEP 484 string annotation) to defer resolution.
Audit all other TYPE_CHECKING-guarded names in `src/hub/dependencies.py` and similar files for
the same pattern.
