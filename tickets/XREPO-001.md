# XREPO-001: Cross-repo search and global context query

## Summary

Implement global context and search flows that aggregate approved results across multiple indexed repos.

## Wave

4

## Lane

cross-repo

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: suspect
- source_ticket_id: None
- source_mode: None

## Depends On

CTX-002, CTX-003

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Cross-repo query path is defined
- [ ] Per-repo access controls still apply
- [ ] Returned results keep repo-level provenance

## Artifacts

- plan: .opencode/state/plans/xrepo-001-planning-plan.md (planning) - Implementation plan for XREPO-001: Cross-repo search and global context query. Defines 3 new MCP tools (search_across_repos, list_related_repos, get_project_landscape), access control via RepoRepository, provenance preservation with repo_id/node_id in results, new files (cross_repo_service.py, cross_repo.py), and modifications to models.py and tools/__init__.py. All acceptance criteria addressed - no blockers.
- implementation: .opencode/state/implementations/xrepo-001-implementation-implementation.md (implementation) - Implementation of XREPO-001: Cross-repo search and global context query. Created cross_repo_service.py and cross_repo.py, added models to models.py, registered 3 new MCP tools.
- review: .opencode/state/reviews/xrepo-001-review-review.md (review) - Approved
- qa: .opencode/state/qa/xrepo-001-qa-qa.md (qa) - Passed
- backlog-verification: .opencode/state/reviews/xrepo-001-review-backlog-verification.md (review) - Backlog verification for XREPO-001: PASS

## Notes


