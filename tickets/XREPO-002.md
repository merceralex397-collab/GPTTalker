# XREPO-002: Repo relationships and landscape metadata

## Summary

Track repo-to-repo relationships and shared metadata needed for landscape views and architecture-level navigation.

## Wave

4

## Lane

cross-repo

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

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

CORE-002, CTX-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Relationship metadata model is explicit
- [ ] Landscape metadata has a structured owner
- [ ] Cross-repo views can cite their source records

## Artifacts

- plan: .opencode/state/plans/xrepo-002-planning-plan.md (planning) - Implementation plan for XREPO-002: Repo relationships and landscape metadata. Defines explicit relationship metadata model (RepoRelationship, RelationshipType, RepoOwner), structured landscape ownership (LandscapeMetadata with owner/maintainers), and citable source records (LandscapeSource). Creates new relationship service, repository, MCP tools, and extends existing cross-repo service with owner and citation data.
- implementation: .opencode/state/implementations/xrepo-002-implementation-implementation.md (implementation) - Implementation of XREPO-002: Created relationship repository, relationship service, and MCP tool handlers. Added relationship and owner models to models.py, updated tables.py and migrations.py for new schema v3, extended cross_repo_service.py with owner metadata and source citations.
- review: .opencode/state/reviews/xrepo-002-review-review.md (review) - Approved
- qa: .opencode/state/qa/xrepo-002-qa-qa.md (qa) - Passed
- backlog-verification: .opencode/state/reviews/xrepo-002-review-backlog-verification.md (review) - Backlog verification for XREPO-002: PASS

## Notes


