# CORE-006: MCP tool routing framework

## Summary

Create the hub-side tool routing framework that maps exposed MCP tools to validated execution paths and shared response formatting.

## Wave

1

## Lane

hub-core

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- finding_source: None
- source_ticket_id: None
- source_mode: None

## Depends On

SETUP-004, CORE-002, CORE-005

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Tool registration boundary is defined
- [ ] Routing integrates policy checks before execution
- [ ] Shared error formatting follows the MCP-safe contract

## Artifacts

- planning: .opencode/state/plans/core-006-planning-planning.md (planning) - Implementation plan for CORE-006: MCP tool routing framework. Defines policy-integrated tool routing with PolicyRequirement declarations, PolicyAwareToolRouter for policy validation before handler execution, and MCP-safe error formatting using JSON-RPC 2.0 error codes. Creates 4 new files and modifies 4 existing files.
- implementation: .opencode/state/implementations/core-006-implementation-implementation.md (implementation) - Implementation of CORE-006: Created MCP tool routing framework with PolicyAwareToolRouter, PolicyRequirement dataclass, MCP error formatting, and DI providers. Added policy field to ToolDefinition and updated MCPProtocolHandler to use policy-aware routing.
- review: .opencode/state/reviews/core-006-review-review.md (review) - Fix verification for CORE-006: Policy default now correctly returns READ_NODE_REQUIREMENT instead of None, enforcing fail-closed validation for all tools without explicit policy declarations.
- qa: .opencode/state/qa/core-006-qa-qa.md (qa) - QA verification for CORE-006: All 3 acceptance criteria verified via code inspection - tool registration boundary defined, policy integration before execution confirmed, MCP-safe error formatting with JSON-RPC 2.0 codes implemented.
- backlog-verification: .opencode/state/reviews/core-006-review-backlog-verification.md (review) - Backlog verification for CORE-006: PASS
- reverification: .opencode/state/artifacts/history/core-006/review/2026-03-31T21-25-18-177Z-reverification.md (review) - Trust restored using CORE-006.

## Notes


