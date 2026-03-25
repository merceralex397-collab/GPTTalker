# EXEC-011: Reduce repo-wide ruff violations to zero

## Summary

Repo-managed linting is now executable and currently reports 51 Ruff violations across source and tests. Normalize imports, remove dead code, and align FastAPI/typing patterns so `ruff check .` becomes a usable gate again.

## Wave

10

## Lane

hardening

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: EXEC-002
- source_mode: post_completion_issue

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` exits 0.
- [ ] Import ordering, unused imports, and mechanical style issues are cleaned up without changing runtime behavior.
- [ ] FastAPI dependency patterns stay consistent with repo policy and current B008 handling rules.
- [ ] If the work is too broad for one session, the planning artifact must split it into narrower follow-up tickets before implementation.

## Artifacts

- None yet

## Notes

- Evidence source: post-repair lint verification on 2026-03-25 reported 51 Ruff findings.

