# REMED-012: Remediation review artifact does not contain runnable command evidence

## Summary

Remediate EXEC-REMED-001 by correcting the validated issue and rerunning the relevant quality checks. Affected surfaces: tickets/manifest.json, .opencode/state/reviews/fix-020-review-ticket-reconciliation.md.

## Wave

31

## Lane

remediation

## Parallel Safety

- parallel_safe: false
- overlap_risk: low

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: trusted
- finding_source: EXEC-REMED-001
- source_ticket_id: REMED-007
- source_mode: split_scope

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] The validated finding `EXEC-REMED-001` no longer reproduces.
- [ ] Current quality checks rerun with evidence tied to the fix approach: For remediation tickets with `finding_source`, require the review artifact to record the exact command run, include raw command output, and state the explicit PASS/FAIL result before the review counts as trustworthy closure.

## Artifacts

- plan: .opencode/state/artifacts/history/remed-012/planning/2026-04-13T22-10-14-162Z-plan.md (planning) - Plan for REMED-012: finding EXEC-REMED-001 is stale — all fixes confirmed present, no code changes required
- plan_review: .opencode/state/artifacts/history/remed-012/plan-review/2026-04-13T22-10-58-524Z-plan-review.md (plan_review) - Plan review for REMED-012: APPROVED — finding is stale, no code changes required
- implementation: .opencode/state/artifacts/history/remed-012/implementation/2026-04-13T22-13-05-373Z-implementation.md (implementation) - REMED-012 implementation: finding EXEC-REMED-001 is STALE, all fixes confirmed present, no code changes required. QA section with import verification commands included.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T22-14-31-576Z-review.md (review) [superseded] - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. All remediation chain fixes confirmed present. QA section with 3 import verification commands and explicit PASS results included.
- qa: .opencode/state/artifacts/history/remed-012/qa/2026-04-13T22-16-12-057Z-qa.md (qa) - QA verification for REMED-012: All 3 import verification commands PASS. Finding EXEC-REMED-001 is STALE. All acceptance criteria verified.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T22-26-09-064Z-review.md (review) [superseded] - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. All remediation chain fixes confirmed present. QA section with 5 verification commands and explicit PASS results included.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T22-28-50-059Z-review.md (review) [superseded] - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. All remediation chain fixes confirmed present. QA section with 5 verification commands and explicit PASS results included.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T22-29-43-770Z-review.md (review) [superseded] - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. All fixes confirmed present. QA section with 5 import verification commands (uv run python -c style) and explicit PASS results included.
- smoke-test: .opencode/state/artifacts/history/remed-012/smoke-test/2026-04-13T22-30-22-405Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T23-19-27-899Z-review.md (review) [superseded] - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. All fixes confirmed present. QA section with 3 inline smoke-test commands, actual raw output embedded, and explicit PASS results.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T23-20-16-263Z-review.md (review) [superseded] - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. QA section uses **Command Record N** format with exact commands, raw output embedded inline, and explicit PASS results.
- review: .opencode/state/artifacts/history/remed-012/review/2026-04-13T23-21-13-616Z-review.md (review) - Review artifact for REMED-012: Finding EXEC-REMED-001 is STALE. QA section uses structured stdout/stderr sections per command, raw output embedded inline, explicit PASS results.
- backlog-verification: .opencode/state/artifacts/history/remed-012/review/2026-04-16T11-37-27-640Z-backlog-verification.md (review) - Backlog verification for REMED-012: PASS. Finding EXEC-REMED-001 is STALE, smoke-test 131/131 PASS, 5 import verification commands PASS, all remediation chain fixes confirmed present.

## Notes


