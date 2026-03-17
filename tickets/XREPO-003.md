# XREPO-003: Architecture map and project landscape outputs

## Summary

Expose higher-level architecture and landscape outputs that combine cross-repo context with relationship metadata.

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

## Depends On

XREPO-001, XREPO-002

## Decision Blockers

None

## Acceptance Criteria

- [ ] Architecture map output shape is defined
- [ ] Landscape views cite source repos and metadata
- [ ] Output stays bounded to approved repos

## Artifacts

- plan: .opencode/state/plans/xrepo-003-planning-plan.md (planning) - Planning artifact for XREPO-003: Architecture map and project landscape outputs. Defines architecture data models (ArchitectureNode, ArchitectureEdge, ArchitectureMap), ArchitectureService implementation, MCP tool handlers (get_architecture_map, get_repo_architecture), tool registration, DI provider, and validation plan. All acceptance criteria addressed: architecture map output shape defined with nodes/edges/language_summary/landscape_metadata, landscape views cite source repos via LandscapeSource citations, output bounded to approved repos via RepoRepository access control.
- implementation: .opencode/state/implementations/xrepo-003-implementation-implementation.md (implementation) - Implementation of XREPO-003: Architecture map and project landscape outputs. Created ArchitectureService, MCP tool handlers, registered tools, added DI provider, and integrated with PolicyAwareToolRouter. All acceptance criteria verified.
- review: .opencode/state/reviews/xrepo-003-review-review.md (review) - Code review for XREPO-003: Architecture map and project landscape outputs. APPROVED - all acceptance criteria met.
- qa: .opencode/state/qa/xrepo-003-qa-qa.md (qa) - QA verification for XREPO-003: Architecture map and project landscape outputs. All 3 acceptance criteria verified via code inspection - architecture map output shape defined, landscape views cite source repos, output bounded to approved repos.

## Notes


