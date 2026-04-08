# REPO-001: list_nodes and list_repos tools

## Summary

Implement the top-level discovery tools that expose registered nodes and their approved repos to ChatGPT.

## Wave

2

## Lane

repo-inspection

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- source_ticket_id: None
- source_mode: None

## Depends On

CORE-001, CORE-004, CORE-006

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Nodes list with health metadata is available
- [ ] Repo discovery reflects approved registry state only
- [ ] Unauthorized targets are excluded

## Artifacts

- plan: .opencode/state/plans/repo-001-planning-plan.md (planning) - Implementation plan for REPO-001: list_nodes and list_repos tools. Defines two MCP discovery tools - list_nodes returns registered nodes with health metadata, list_repos returns approved repos optionally filtered by node_id. Creates 2 new files (tools/__init__.py, tools/discovery.py), modifies 2 existing files (schemas.py, main.py). Integrates with existing NodeRepository, RepoRepository, and PolicyAwareToolRouter. Uses NO_POLICY_REQUIREMENT for list_nodes and READ_NODE_REQUIREMENT for list_repos.
- review: .opencode/state/reviews/repo-001-review-review.md (review) - Plan review for REPO-001: APPROVED. All 3 acceptance criteria verified - nodes list with health metadata, repo discovery from registry only, unauthorized targets excluded via policy. Integration points confirmed against existing codebase.
- implementation: .opencode/state/implementations/repo-001-implementation-implementation.md (implementation) - Fixed REPO-001 implementation: Fixed non-functional handlers and added DI integration. Updated discovery.py handlers to use actual implementations, modified PolicyAwareToolRouter to inject repositories, and updated dependencies.py to provide repositories to the router.
- qa: .opencode/state/qa/repo-001-qa-qa.md (qa) - QA verification for REPO-001: All 3 acceptance criteria verified - nodes list with health metadata, repo discovery from registry only, and unauthorized targets excluded via READ_NODE_REQUIREMENT policy.
- backlog-verification: .opencode/state/reviews/repo-001-review-backlog-verification.md (review) - Backlog verification for REPO-001: PASS
- reverification: .opencode/state/artifacts/history/repo-001/review/2026-03-31T21-25-30-634Z-reverification.md (review) - Trust restored using REPO-001.

## Notes


