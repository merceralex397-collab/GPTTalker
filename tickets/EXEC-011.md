# EXEC-011: Reduce repo-wide ruff violations to zero

## Summary

EXEC-011 closeout: repo-wide ruff violations reduced to zero. Objective achieved via split execution of EXEC-013 (alias fixes) and EXEC-014 (mechanical violations). ruff check . exits 0.

## Wave

10

## Lane

hardening

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
- source_ticket_id: EXEC-002
- source_mode: post_completion_issue

## Depends On

None

## Follow-up Tickets

- EXEC-013
- EXEC-014

## Decision Blockers

- Execution split into follow-up tickets EXEC-013 and EXEC-014; keep this parent ticket non-foreground until the child tickets land.

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` exits 0.
- [ ] Import ordering, unused imports, and mechanical style issues are cleaned up without changing runtime behavior.
- [ ] FastAPI dependency patterns stay consistent with repo policy and current B008 handling rules.
- [ ] If the work is too broad for one session, the planning artifact must split it into narrower follow-up tickets before implementation.

## Artifacts

- plan: .opencode/state/plans/exec-011-planning-plan.md (planning) - Planning artifact for EXEC-011: Reduce repo-wide ruff violations to zero. Identifies 51 violations across 5 categories: UP038 datetime.utcnow deprecation (~30), duplicate imports (~5), unused imports (~10), import ordering (~5), and 1 stray syntax artifact. Recommends splitting into 2 follow-up tickets (EXEC-013 for datetime fixes, EXEC-014 for import/mechanical fixes).
- implementation: .opencode/state/artifacts/history/exec-011/implementation/2026-03-27T16-29-32-073Z-implementation.md (implementation) - EXEC-011 implementation documenting the split execution of EXEC-013 (alias fixes) and EXEC-014 (mechanical violations). Final outcome: ruff check . exits 0.
- review: .opencode/state/artifacts/history/exec-011/review/2026-03-27T16-30-23-270Z-review.md (review) - Code review for EXEC-011: APPROVED. Child tickets EXEC-013 and EXEC-014 verified complete. All acceptance criteria satisfied.
- qa: .opencode/state/artifacts/history/exec-011/qa/2026-03-27T16-30-54-120Z-qa.md (qa) - QA verification for EXEC-011: PASS. Both child tickets verified complete, ruff check . exits 0 confirmed.
- smoke-test: .opencode/state/artifacts/history/exec-011/smoke-test/2026-03-27T16-31-04-166Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test passed.
- reverification: .opencode/state/artifacts/history/exec-011/review/2026-03-28T12-39-37-363Z-reverification.md (review) - Trust restored using EXEC-014.
- backlog-verification: .opencode/state/artifacts/history/exec-011/review/2026-03-28T16-28-26-361Z-backlog-verification.md (review) - Backlog verification for EXEC-011: PASS. All acceptance criteria verified via smoke-test artifacts and corroborating evidence from EXEC-013/EXEC-014.
- smoke-test: .opencode/state/artifacts/history/exec-011/smoke-test/2026-03-28T16-32-27-376Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-011/bootstrap/2026-03-28T16-33-16-169Z-environment-bootstrap.md (bootstrap) - Environment bootstrap completed successfully.
- smoke-test: .opencode/state/artifacts/history/exec-011/smoke-test/2026-03-28T16-39-25-444Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.

## Notes

- Evidence source: post-repair lint verification on 2026-03-25 reported 51 Ruff findings.
- Current canonical child tickets are EXEC-013 and EXEC-014. Use the child tickets for active implementation; do not resume this parent directly while the split remains open.

