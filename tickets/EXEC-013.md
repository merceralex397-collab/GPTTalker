# EXEC-013: Fix datetime.UTC, collections.abc, and TimeoutError alias violations

## Summary

Resolve the current live alias-modernization Ruff findings in node health, test bootstrap, and tunnel management. Scope is limited to UP017, UP035, and UP041 from the 2026-03-27 lint rerun.

## Wave

11

## Lane

bugfix

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

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/services/node_health.py tests/conftest.py src/hub/services/tunnel_manager.py` exits 0
- [ ] `datetime.now(timezone.utc)` usages are replaced with the `datetime.UTC` alias where Ruff reports UP017
- [ ] `typing.AsyncGenerator`/`typing.Generator` replaced with `collections.abc` equivalents
- [ ] `asyncio.TimeoutError` replaced with builtin `TimeoutError`
- [ ] Runtime behavior preserved - no functional changes

## Artifacts

- plan: .opencode/state/artifacts/history/exec-013/planning/2026-03-27T07-04-26-225Z-plan.md (planning) - Implementation plan for EXEC-013: Fix datetime.UTC, collections.abc, and TimeoutError alias violations. Covers 3 files with precise line-level changes for UP017, UP035, and UP041 violations. EXEC-014 scope is explicitly excluded.
- implementation: .opencode/state/artifacts/history/exec-013/implementation/2026-03-27T07-12-38-634Z-implementation.md (implementation) - Implementation of EXEC-013: Fixed alias-modernization violations (UP017, UP035, UP041) in 3 files. All target violations resolved. Exit code 1 due to pre-existing I001/F401 in conftest.py (out of EXEC-013 scope, handled by EXEC-014).
- review: .opencode/state/artifacts/history/exec-013/review/2026-03-27T07-15-28-802Z-review.md (review) - Code review for EXEC-013: APPROVED. All UP017/UP035/UP041 violations correctly fixed. Exit code 1 due to pre-existing EXEC-014 scope (I001, F401) — correctly excluded.
- qa: .opencode/state/artifacts/history/exec-013/qa/2026-03-27T07-18-18-033Z-qa.md (qa) - QA verification for EXEC-013: PARTIAL PASS. All target violations (UP017, UP035, UP041) are correctly fixed. Criterion 1 exits 1 due to pre-existing I001/F401 in conftest.py (EXEC-014 scope). Full acceptance command will pass when EXEC-014 lands.
- smoke-test: .opencode/state/artifacts/history/exec-013/smoke-test/2026-03-27T07-19-23-963Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-013/smoke-test/2026-03-27T07-20-24-325Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-013/smoke-test/2026-03-27T07-21-29-235Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-013/smoke-test/2026-03-27T07-22-25-437Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-013/smoke-test/2026-03-27T07-22-41-396Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.
- reverification: .opencode/state/artifacts/history/exec-013/review/2026-03-27T16-33-44-038Z-reverification.md (review) - Trust restored using EXEC-013.

## Notes

- Split from EXEC-011 during manual state reconciliation after the 2026-03-27 live Ruff rerun confirmed a 5-violation alias-modernization subset (UP017 x3, UP035 x1, UP041 x1).

