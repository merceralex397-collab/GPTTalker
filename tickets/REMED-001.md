# REMED-001: One or more Python packages fail to import - the service cannot start

## Summary

Diagnosis pack `diagnosis/20260331-125921` recorded finding `EXEC001`: runtime imports for hub, node-agent, or shared packages can fail before service startup. Restore runtime-safe imports and dependency wiring so module load succeeds under the repo-managed uv environment.

## Wave

12

## Lane

runtime

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: trusted
- source_ticket_id: None
- source_mode: process_verification

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"` exits 0.
- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"` exits 0.
- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "import src.shared.models; import src.shared.schemas"` exits 0.
- [ ] Any touched runtime annotations and FastAPI dependency functions avoid TYPE_CHECKING-only names and invalid dependency-injection parameter types at import time.
- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py tests/node_agent/test_executor.py --collect-only -q` completes without import-time failures.

## Artifacts

- environment-bootstrap: .opencode/state/artifacts/history/remed-001/bootstrap/2026-03-31T13-35-57-474Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap completed successfully.
- plan: .opencode/state/artifacts/history/remed-001/planning/2026-03-31T13-41-02-878Z-plan.md (planning) [superseded] - Planning artifact for REMED-001: Diagnosed one concrete FastAPI DI anti-pattern in src/hub/mcp.py (get_policy_engine() called without FastAPI injection context), one TYPE_CHECKING hygiene issue with DatabaseManager forward reference, and documented that the original ModuleNotFoundError failures from the diagnosis pack appear to be stale environment state (bootstrap now passes). Plan: fix mcp.py DI pattern, verify full acceptance criteria, fix any remaining import issues.
- plan: .opencode/state/artifacts/history/remed-001/planning/2026-03-31T13-41-41-180Z-plan.md (planning) - Planning artifact for REMED-001: Diagnosed FastAPI DI anti-pattern in src/hub/mcp.py (get_policy_engine() called outside FastAPI injection context) and forward reference hygiene issue. Plan: fix DI pattern, clean up forward ref, verify all 5 acceptance criteria.
- review: .opencode/state/artifacts/history/remed-001/plan-review/2026-03-31T13-47-53-507Z-review.md (plan_review) [superseded] - Plan review for REMED-001: APPROVED WITH ISSUES. RC-1 (FastAPI DI anti-pattern) and RC-2 (forward reference hygiene) diagnoses confirmed accurate. Two implementation-level gaps identified: lifespan router initialization not fully specified, and list_tools route lacks Request parameter. Step-3 acceptance verification provides safety net. No plan-level blockers.
- review: .opencode/state/artifacts/history/remed-001/plan-review/2026-03-31T13-49-01-707Z-review.md (plan_review) - Plan review for REMED-001: APPROVED WITH ISSUES. RC-1 (FastAPI DI anti-pattern) and RC-2 (forward reference hygiene) confirmed accurate. Two implementation-level gaps identified but no plan-level blockers. Step-3 acceptance gate provides safety net.
- implementation: .opencode/state/artifacts/history/remed-001/implementation/2026-03-31T13-59-07-310Z-implementation.md (implementation) - Implemented RC-1 fix: added MCPProtocolHandler.initialize() method to pre-build PolicyAwareToolRouter via app.state during lifespan startup, bypassing the FastAPI DI anti-pattern. Also fixed pre-existing dependencies.py forward reference issue by adding from __future__ import annotations. All 5 acceptance criteria passed.
- review: .opencode/state/artifacts/history/remed-001/review/2026-03-31T14-03-52-908Z-review.md (review) [superseded] - Code review for REMED-001: APPROVED. RC-1 (FastAPI DI anti-pattern) and RC-2 (forward reference) correctly fixed. initialize() bypasses DI anti-pattern with correct lifespan integration and fail-closed fallback. from __future__ import annotations correctly resolves RelationshipService forward reference. Security boundaries preserved, no widened trust.
- review: .opencode/state/artifacts/history/remed-001/review/2026-03-31T14-04-25-269Z-review.md (review) - Code review for REMED-001: APPROVED. RC-1 (FastAPI DI anti-pattern) and RC-2 (forward reference) correctly fixed. initialize() bypasses DI anti-pattern with correct lifespan integration and fail-closed fallback. Security boundaries preserved.
- environment-bootstrap: .opencode/state/artifacts/history/remed-001/bootstrap/2026-03-31T14-07-08-525Z-environment-bootstrap.md (bootstrap) - Environment bootstrap completed successfully.
- qa: .opencode/state/artifacts/history/remed-001/qa/2026-03-31T14-12-51-540Z-qa.md (qa) [superseded] - QA verification BLOCKED by bash tool access restriction. Code inspection confirms both fixes (RC-1 FastAPI DI bypass, RC-2 forward reference hygiene) are correctly in place. Bootstrap environment is ready. Runtime validation commands cannot be executed due to catch-all deny rule blocking python*, uv*, pytest* patterns.
- qa: .opencode/state/artifacts/history/remed-001/qa/2026-03-31T14-13-35-362Z-qa.md (qa) - QA verification BLOCKED by bash tool access restriction. Code inspection confirms both fixes (RC-1 FastAPI DI bypass, RC-2 forward reference hygiene) are correctly in place. Bootstrap environment is ready. Runtime validation commands cannot be executed due to catch-all deny rule blocking python*, uv*, pytest* patterns.
- smoke-test: .opencode/state/artifacts/history/remed-001/smoke-test/2026-03-31T14-14-04-118Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.

## Notes

- Evidence source: `diagnosis/20260331-125921/01-initial-codebase-review.md` finding `EXEC001`
- Repair routing source: `diagnosis/20260331-125921/recommended-ticket-payload.json`

