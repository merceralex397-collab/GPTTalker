# EDGE-003: Replace Cloudflare public edge with ngrok runtime and config

## Summary

Replace Cloudflare-specific public-edge configuration, runtime management, and operator documentation with the ngrok architecture accepted in the March 31 pivot. The ngrok migration was already substantially complete in all runtime surfaces; the only remaining gap was the missing TunnelManager export, which was added to src/hub/services/__init__.py.

## Wave

12

## Lane

edge

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: trusted
- finding_source: None
- source_ticket_id: EDGE-001
- source_mode: post_completion_issue

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Hub config exposes ngrok-specific public-edge settings instead of Cloudflare-specific fields
- [ ] Hub startup and tunnel runtime management launch or detect ngrok rather than cloudflared
- [ ] Operator documentation describes ngrok as the canonical public-edge setup path
- [ ] Validation covers ngrok command construction or runtime health behavior at least at unit-test level

## Artifacts

- plan: .opencode/state/artifacts/history/edge-003/planning/2026-03-31T14-29-19-520Z-plan.md (planning) - Planning for EDGE-003: ngrok migration already complete in all runtime surfaces. Single remaining gap: TunnelManager not exported from src/hub/services/__init__.py. Plan: add the missing export.
- implementation: .opencode/state/artifacts/history/edge-003/implementation/2026-03-31T14-33-02-126Z-implementation.md (implementation) - Implementation of EDGE-003: Added TunnelManager export to src/hub/services/__init__.py. All 4 acceptance criteria passed.
- review: .opencode/state/artifacts/history/edge-003/review/2026-03-31T14-34-17-593Z-review.md (review) - Code review for EDGE-003: APPROVED. TunnelManager export correctly added. All acceptance criteria met by existing runtime surfaces.
- qa: .opencode/state/artifacts/history/edge-003/qa/2026-03-31T14-36-50-688Z-qa.md (qa) - QA verification for EDGE-003: All 4 acceptance criteria verified via code inspection and import test. ngrok migration confirmed complete in all runtime surfaces.
- smoke-test: .opencode/state/artifacts/history/edge-003/smoke-test/2026-03-31T14-37-07-458Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/edge-003/smoke-test/2026-03-31T14-37-58-988Z-smoke-test.md (smoke-test) - Deterministic smoke test passed.
- ticket-reconciliation: .opencode/state/artifacts/history/edge-003/review/2026-03-31T21-14-36-116Z-ticket-reconciliation.md (review) [superseded] - Reconciled EDGE-001 against EDGE-003.
- ticket-reconciliation: .opencode/state/artifacts/history/edge-003/review/2026-03-31T21-14-46-296Z-ticket-reconciliation.md (review) - Reconciled EDGE-002 against EDGE-003.
- backlog-verification: .opencode/state/artifacts/history/edge-003/review/2026-04-10T00-40-37-275Z-backlog-verification.md (review) - Backlog verification for EDGE-003: PASS — all 4 acceptance criteria verified, ngrok migration complete

## Notes

