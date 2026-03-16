# CORE-005: Policy engine and normalized path validation

## Summary

Build the fail-closed policy engine for nodes, repos, write targets, service aliases, and normalized file paths.

## Wave

1

## Lane

security

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

planning

## Status

todo

## Depends On

SETUP-002, SETUP-004

## Decision Blockers

None

## Acceptance Criteria

- [ ] Unknown targets are rejected explicitly
- [ ] Path normalization rules are central and reusable
- [ ] Write and read scopes are separated cleanly

## Artifacts

- None yet

## Notes


