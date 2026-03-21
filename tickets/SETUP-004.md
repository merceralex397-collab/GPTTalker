# SETUP-004: FastAPI hub app shell and MCP transport baseline

## Summary

Create the initial FastAPI application shell for the hub, including startup structure, dependency injection, and MCP-facing request routing primitives.

## Wave

0

## Lane

hub-core

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

closeout

## Status

done

## Depends On

SETUP-001, SETUP-002

## Decision Blockers

None

## Acceptance Criteria

- [ ] Hub app entrypoint and package shape are defined
- [ ] MCP-facing transport boundary is explicit
- [ ] Startup path leaves room for policy and registry injection

## Artifacts

- planning: .opencode/state/plans/setup-004-planning-planning.md (planning) - Implementation plan for SETUP-004: FastAPI hub app shell and MCP transport baseline. Defines complete FastAPI app with lifespan, dependency injection for database/config/logging, MCP transport layer with tool handler primitives, tool routing registry, and MCP-facing HTTP endpoints.
- implementation: .opencode/state/implementations/setup-004-implementation-implementation.md (implementation) - Implementation of SETUP-004: FastAPI hub app shell and MCP transport baseline. Created dependencies.py, lifespan.py, transport layer (base.py, mcp.py, __init__.py), tool_router.py, and completed main.py, mcp.py, routes.py, config.py. All lint checks pass.
- review: .opencode/state/reviews/setup-004-review-review.md (review) - Code review for SETUP-004: Approved. Implementation matches plan - all 6 new files created, all 4 files modified as planned. Acceptance criteria satisfied: hub app entrypoint defined, MCP transport boundary explicit, startup path leaves room for policy/registry injection. Code quality high with complete type hints and docstrings.
- qa: .opencode/state/qa/setup-004-qa-qa.md (qa) - QA verification for SETUP-004: All 3 acceptance criteria verified - hub app entrypoint, MCP transport boundary, and startup injection hooks all pass. Code quality confirmed via static analysis.
- backlog-verification: .opencode/state/reviews/setup-004-review-backlog-verification.md (review) - Backlog verification for SETUP-004: PASS

## Notes


