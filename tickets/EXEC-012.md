# EXEC-012: Fix misclassified paths in test_path_traversal_dotdot_rejected and test_invalid_path_rejected

## Summary

Two security tests incorrectly classify valid paths as dangerous: (1) test_path_traversal_dotdot_rejected includes `....` and `.../...` which do NOT escape the base directory and should not be rejected; (2) test_invalid_path_rejected includes `foo/./bar` which normalizes to `foo/bar` (in-bounds) and should not be rejected. The security code in path_utils.py and inspection.py is correct. Only test expectations need correction. Fix discovered during EXEC-008 smoke-test closeout.

## Wave

11

## Lane

bugfix

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

## Stage

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: EXEC-008
- source_mode: net_new_scope

## Depends On

EXEC-008

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] test_path_traversal_dotdot_rejected passes with `....` and `.../...` removed from dangerous_paths list
- [ ] test_invalid_path_rejected passes with `foo/./bar` removed from invalid_paths list
- [ ] UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py tests/hub/test_contracts.py -q --tb=no exits 0

## Artifacts

- None yet

## Notes

- Evidence source: EXEC-008 smoke-test closeout and 2026-03-27 Scafforge repair verification.
- Evidence refreshed on 2026-03-27: the full suite still includes the path-scope mismatch owned here, while `tests/hub/test_contracts.py::TestFailureModes::test_invalid_path_rejected` now passes under the current contract.
