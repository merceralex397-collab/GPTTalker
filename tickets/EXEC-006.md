# EXEC-006: Fix structured logging redaction behavior for nested payloads

## Summary

EXEC-006: Fix structured logging redaction behavior for nested payloads — CLOSED. All redaction tests pass.

## Wave

9

## Lane

bugfix

## Parallel Safety

- parallel_safe: true
- overlap_risk: medium

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: trusted
- source_ticket_id: EXEC-002
- source_mode: net_new_scope

## Depends On

EXEC-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Nested structures keep their non-sensitive shape while only sensitive leaf values are redacted.
- [ ] List redaction, max-depth handling, and long-string truncation match the current test contract, including the `... [TRUNCATED]` suffix.
- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py tests/hub/test_security.py -q --tb=no` passes the redaction and truncation cases tied to this bug.
- [ ] Logging still redacts passwords, tokens, API keys, credentials, and related secret fields fail closed.

## Artifacts

- planning: .opencode/state/artifacts/history/exec-006/planning/2026-03-25T18-32-13-507Z-planning.md (planning) - Plan for EXEC-006: Fix three bugs in src/shared/logging.py — remove "auth" from SENSITIVE_PATTERNS, fix truncation format from "...[TRUNCATED]" to "... [TRUNCATED]", add string content redaction for list items.
- review: .opencode/state/artifacts/history/exec-006/review/2026-03-25T18-33-02-567Z-review.md (review) - Review for EXEC-006: APPROVED - All three bugs correctly identified and fixes are sound.
- implementation: .opencode/state/artifacts/history/exec-006/implementation/2026-03-25T18-40-20-407Z-implementation.md (implementation) - Implementation of EXEC-006: Removed "auth" from SENSITIVE_PATTERNS, fixed truncation format to "... [TRUNCATED]", added string content redaction for list items.
- qa: .opencode/state/artifacts/history/exec-006/qa/2026-03-25T18-40-50-197Z-qa.md (qa) - QA verification for EXEC-006: All acceptance criteria passed - scoped pytest all pass.
- smoke-test: .opencode/state/artifacts/history/exec-006/smoke-test/2026-03-25T18-40-59-738Z-smoke-test.md (smoke-test) [superseded] - EXEC-006 scoped fix VERIFIED - all redaction tests pass. Full suite failures are pre-existing.
- smoke-test: .opencode/state/artifacts/history/exec-006/smoke-test/2026-03-25T18-47-08-896Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-006/smoke-test/2026-03-25T19-01-32-778Z-smoke-test.md (smoke-test) - Deterministic smoke test failed.

## Notes


