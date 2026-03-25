# EXEC-001: Fix node-agent FastAPI dependency injection import failure

## Summary

Audit reproduced a node-agent import failure on March 24, 2026 in the repo virtualenv. `.venv/bin/python -c "from src.node_agent.main import app"` fails with `fastapi.exceptions.FastAPIError: Invalid args for response field!` because `src/node_agent/dependencies.py` exposes `app: FastAPI` in dependency providers instead of pulling app state from `Request`. Fix the dependency-injection pattern so the node agent imports cleanly.

## Wave

9

## Lane

bugfix

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

smoke_test

## Status

smoke_test

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: None
- source_mode: net_new_scope

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Replace FastAPI app injection in `src/node_agent/dependencies.py` with a FastAPI-safe dependency pattern based on `Request` or equivalent runtime-safe access to app state.
- [ ] `.venv/bin/python -c "from src.node_agent.main import app"` exits 0.
- [ ] The fix does not widen node-agent trust boundaries or bypass existing path validation.
- [ ] `.venv/bin/pytest tests/ --collect-only -q --tb=no` no longer fails on node-agent import wiring.

## Artifacts

- environment-bootstrap: .opencode/state/artifacts/history/exec-001/bootstrap/2026-03-25T00-23-01-839Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-001/bootstrap/2026-03-25T00-25-27-142Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-001/bootstrap/2026-03-25T00-27-14-512Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-001/bootstrap/2026-03-25T01-39-52-323Z-environment-bootstrap.md (bootstrap) - Environment bootstrap failed.
- planning: .opencode/state/artifacts/history/exec-001/planning/2026-03-25T03-46-32-997Z-planning.md (planning) - Plan for EXEC-001: Fix node-agent FastAPI dependency injection import failure. Replaces `app: FastAPI` in get_config/get_executor with `request: Request` and accesses app state via `request.app.state`. Changes only dependencies.py; health.py and operations.py need no structural changes as FastAPI auto-resolves Request in dependency functions.
- implementation: .opencode/state/artifacts/history/exec-001/implementation/2026-03-25T03-55-27-215Z-implementation.md (implementation) - Implementation of EXEC-001: Fixed node-agent FastAPI dependency injection by replacing app: FastAPI with request: Request pattern. All validation commands pass (import test, pytest collection with 126 tests, ruff lint check).
- review: .opencode/state/artifacts/history/exec-001/review/2026-03-25T03-57-37-327Z-review.md (review) - Code review for EXEC-001: APPROVED. All acceptance criteria verified - get_config/get_executor use request: Request pattern, app state accessed via request.app.state, no changes to executor path validation, all 3 validation commands passed.
- qa: .opencode/state/artifacts/history/exec-001/qa/2026-03-25T03-59-39-479Z-qa.md (qa) - QA verification for EXEC-001: All 4 acceptance criteria PASSED. Import test exits 0, pytest collection passes with 126 tests, _validate_path trust boundary unchanged, Request pattern correctly implemented.
- smoke-test: .opencode/state/artifacts/history/exec-001/smoke-test/2026-03-25T04-00-18-894Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-001/smoke-test/2026-03-25T04-01-16-155Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test for EXEC-001: PASS. Node-agent import succeeds (exit 0), pytest collection passes (126 tests), ruff passes. Note: default smoke-test tool uses system python which lacks pytest; corrected commands use repo venv as required by EXEC-001 acceptance criteria.
- smoke-test: .opencode/state/artifacts/history/exec-001/smoke-test/2026-03-25T04-04-07-243Z-smoke-test.md (smoke-test) - Deterministic smoke test failed.

## Notes


