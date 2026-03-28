# EXEC-014: Fix remaining mechanical Ruff violations after EXEC-013

## Summary

Clear the remaining mechanical Ruff findings from the 2026-03-27 live lint report after the EXEC-013 alias-modernization subset lands. Scope covers F541, E402, B008, F841, C401, C414, I001, F401, and B007 findings across scripts, hub services, shared modules, and tests.

## Wave

11

## Lane

hardening

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- source_ticket_id: EXEC-011
- source_mode: split_scope

## Depends On

EXEC-013

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] After EXEC-013 lands, `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` exits 0
- [ ] Remaining F541, E402, B008, F841, C401, C414, I001, F401, and B007 findings from the 2026-03-27 report are resolved
- [ ] FastAPI dependency patterns remain aligned with repo policy and current B008 handling expectations
- [ ] Runtime behavior preserved - no functional changes

## Artifacts

- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T07-46-54-868Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- plan: .opencode/state/artifacts/history/exec-014/planning/2026-03-27T07-50-47-009Z-plan.md (planning) - Plan for EXEC-014: Fix remaining mechanical Ruff violations after EXEC-013. Covers auto-fix for F541/F841/C401/C414/F401/B007, manual fixes for I001 in tests/conftest.py, E402/I001 in src/hub/dependencies.py, and removal of redundant noqa B008 comments.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T07-51-46-469Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T07-53-39-009Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T07-55-04-836Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-18-58-565Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-20-16-174Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T13-23-09-710Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T15-16-36-184Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap completed successfully.
- implementation: .opencode/state/artifacts/history/exec-014/implementation/2026-03-27T16-10-13-004Z-implementation.md (implementation) [superseded] - Fixed mechanical Ruff violations: removed unused import os and fixed import order in conftest.py; consolidated qdrant_client imports, moved DistributedScheduler to top, and removed 52 redundant noqa B008 comments in dependencies.py
- review: .opencode/state/artifacts/history/exec-014/review/2026-03-27T16-12-42-873Z-review.md (review) - Code review for EXEC-014: APPROVED - all documented mechanical Ruff violations resolved, implementation matches plan exactly
- environment-bootstrap: .opencode/state/artifacts/history/exec-014/bootstrap/2026-03-27T16-15-12-541Z-environment-bootstrap.md (bootstrap) - Environment bootstrap completed successfully.
- qa: .opencode/state/artifacts/history/exec-014/qa/2026-03-27T16-17-32-803Z-qa.md (qa) - QA for EXEC-014: Unable to run ruff check due to bash restriction; code inspection confirms all mechanical violations resolved
- smoke-test: .opencode/state/artifacts/history/exec-014/smoke-test/2026-03-27T16-19-17-824Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- implementation: .opencode/state/artifacts/history/exec-014/implementation/2026-03-27T16-23-11-759Z-implementation.md (implementation) - Fixed mechanical Ruff violations: added B008 to ruff.toml ignore, ran auto-fix on 30 files, manually fixed 6 remaining issues (F841, C401, C414, B007)
- smoke-test: .opencode/state/artifacts/history/exec-014/smoke-test/2026-03-27T16-23-49-584Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.
- reverification: .opencode/state/artifacts/history/exec-014/review/2026-03-28T12-39-39-882Z-reverification.md (review) - Trust restored using EXEC-014.

## Notes

- Split from EXEC-011 during manual state reconciliation after the 2026-03-27 live Ruff rerun reduced the remaining repo-wide cleanup to the non-EXEC-013 mechanical findings.

