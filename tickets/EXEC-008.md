# EXEC-008: Close remaining hub path and write-target security edge cases

## Summary

Full-suite validation still shows hub security edge-case failures: `foo/./bar` is accepted, home-directory expansion is not rejected, traversal errors do not match the contract, and unregistered write-target validation still breaks on the repository interface boundary.

## Wave

10

## Lane

security

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

EXEC-004

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` exits 0.
- [ ] Path normalization rejects `..`, `.` shortcut traversal, and `~` home-expansion inputs with fail-closed traversal errors.
- [ ] `WriteTargetPolicy` rejects unknown targets through its async repository contract without depending on non-awaitable mocks.
- [ ] The fix preserves base-boundary, symlink, and extension-allowlist enforcement.

## Artifacts

- None yet

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.

