# REPO-002: inspect_repo_tree and read_repo_file tools

## Summary

Implement bounded repo tree inspection and file reads through the node-agent path with strict repo and path validation.

## Wave

2

## Lane

repo-inspection

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

closeout

## Status

done

## Depends On

CORE-004, CORE-005, CORE-006

## Decision Blockers

None

## Acceptance Criteria

- [ ] Repo tree inspection is scoped to approved repos
- [ ] File reads reject traversal and unknown paths
- [ ] Responses are structured for MCP use

## Artifacts

- plan: .opencode/state/plans/repo-002-planning-plan.md (planning) - Implementation plan for REPO-002: inspect_repo_tree and read_repo_file tools. Defines hub-side handlers, node-agent implementations, policy integration with PathNormalizer, MCP request/response schemas, and validation approach. Creates 1 new file (src/hub/tools/inspection.py), modifies 4 existing files, and includes unit and integration tests.
- implementation: .opencode/state/implementations/repo-002-implementation-implementation.md (implementation) - Implementation of REPO-002: inspect_repo_tree and read_repo_file tools. Created hub-side handlers, added node client methods, implemented node agent executor, and registered both MCP tools.
- review: .opencode/state/reviews/repo-002-review-review.md (review) - Code review for REPO-002: inspect_repo_tree and read_repo_file tools. APPROVED - all acceptance criteria met: repo tree inspection scoped to approved repos, file reads reject traversal via PathNormalizer + node-agent path validation, responses structured for MCP use. One low-severity observation: duplicate read_file method in node_client.py should be removed.
- qa: .opencode/state/qa/repo-002-qa-qa.md (qa) - QA verification for REPO-002: inspect_repo_tree and read_repo_file tools. All 3 acceptance criteria verified via code inspection - repo scoping to approved repos, path traversal rejection at hub and node-agent layers, and MCP-structured responses.
- backlog-verification: .opencode/state/reviews/repo-002-review-backlog-verification.md (review) - Backlog verification for REPO-002: PASS

## Notes


