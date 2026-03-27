# EXEC-012: Fix misclassified paths in test_path_traversal_dotdot_rejected and test_invalid_path_rejected

## Summary

Superseded ticket. The original scope captured stale evidence about `....`, `.../...`, and `foo/./bar`. Current repo truth no longer matches that failure set, so the remaining path expectation was folded back into EXEC-008.

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

- resolution_state: superseded
- verification_state: invalidated
- source_ticket_id: EXEC-008
- source_mode: post_completion_issue

## Depends On

None

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
- Superseded on 2026-03-27 after current verification showed `tests/hub/test_contracts.py` already passed and the remaining `tests/hub/test_security.py` mismatch no longer matched this ticket's stale failure set.

