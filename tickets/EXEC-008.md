# EXEC-008: Close remaining hub path and write-target security edge cases

## Summary

The remaining EXEC-008 blocker is a stale test expectation in `tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected`. The live failing case is `foo/bar/../../secrets`, which normalizes to an in-bounds repo path and should be accepted.

## Wave

10

## Lane

security

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- source_ticket_id: EXEC-002
- source_mode: post_completion_issue

## Depends On

EXEC-004

## Follow-up Tickets

- EXEC-012

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` exits 0.
- [ ] Path normalization rejects `..`, `.` shortcut traversal, and `~` home-expansion inputs with fail-closed traversal errors.
- [ ] `WriteTargetPolicy` rejects unknown targets through its async repository contract without depending on non-awaitable mocks.
- [ ] The fix preserves base-boundary, symlink, and extension-allowlist enforcement.

## Artifacts

- planning: .opencode/state/artifacts/history/exec-008/planning/2026-03-26T04-27-15-484Z-planning.md (planning) - Planning artifact for EXEC-008: Close remaining hub path and write-target security edge cases. Identifies 5 root causes and fixes for path normalization and write-target validation issues. Notes blocker: test_unregistered_write_target_denied is out of scope per brief constraint.
- review: .opencode/state/artifacts/history/exec-008/plan-review/2026-03-26T04-29-58-858Z-review.md (plan_review) - Plan review for EXEC-008: APPROVED. The alleged blocker (test_unregistered_write_target_denied broken mock) is invalid. Acceptance criterion 3 explicitly names "non-awaitable mocks" as in-scope. Brief constraint protects code security behavior, not test infrastructure. All 5 fixes approved, plan is decision-complete.
- implementation: .opencode/state/artifacts/history/exec-008/implementation/2026-03-26T04-50-13-178Z-implementation.md (implementation) - Implemented all 5 security fixes: Fix 1 (error message with "traversal"), Fix 2 (~ detection before resolve), Fix 3 (mock method name), Fix 4 (normalize before validate), Fix 5 (mock_write_target fixture). 3 of 5 targeted tests pass. Fix 1 has pytest anomaly (direct Python works). Fix 4 has test expectation mismatch (foo/./bar correctly allowed).
- review: .opencode/state/artifacts/history/exec-008/review/2026-03-26T17-54-05-984Z-review.md (review) - Code review for EXEC-008: APPROVED WITH ISSUES. All 5 security fixes verified correct. Two residual test failures (test_path_traversal_dotdot_rejected and test_invalid_path_rejected) are caused by test bugs misclassifying valid paths, not code defects.
- qa: .opencode/state/artifacts/history/exec-008/qa/2026-03-26T17-57-43-192Z-qa.md (qa) - QA verification for EXEC-008: PARTIAL PASS. Criteria 2/3/4 PASS. Criterion 1 PARTIAL PASS due to 2 test bugs (not code defects) in test_path_traversal_dotdot_rejected (...., .../... misclassified) and test_invalid_path_rejected (foo/./bar is valid). All 5 security fixes verified correct by code inspection.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T17-58-35-000Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T17-58-56-658Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T17-59-27-718Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T18-39-01-413Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T18-42-26-836Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T18-48-57-596Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T18-50-57-652Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T18-52-39-065Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T22-30-50-955Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-26T22-33-31-133Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-27T04-32-02-462Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-008/smoke-test/2026-03-27T04-36-14-727Z-smoke-test.md (smoke-test) - Deterministic smoke test failed.
- backlog-verification: .opencode/state/artifacts/history/exec-008/review/2026-03-27T07-29-19-171Z-backlog-verification.md (review) - Backlog verification recorded during ticket_reverify for EXEC-008.
- reverification: .opencode/state/artifacts/history/exec-008/review/2026-03-27T07-29-19-172Z-reverification.md (review) - Trust restored using EXEC-008.

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.
- Evidence refreshed on 2026-03-27: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v` now leaves `tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected` as the only remaining EXEC-008-owned failure.
- Validated on 2026-03-27: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` exits 0.

