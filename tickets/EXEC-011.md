# EXEC-011: Reduce repo-wide ruff violations to zero

## Summary

Repo-managed linting cleanup proved too broad for one lane. This parent ticket now tracks the split into focused follow-up tickets while preserving the repo-wide lint-zero objective.

## Wave

10

## Lane

hardening

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

implementation

## Status

in_progress

## Trust

- resolution_state: open
- verification_state: suspect
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

## Notes

- Evidence source: post-repair lint verification on 2026-03-25 reported 51 Ruff findings.
- Current canonical child tickets are EXEC-013 and EXEC-014. Use the child tickets for active implementation; do not resume this parent directly while the split remains open.

