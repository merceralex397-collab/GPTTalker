# SCHED-002: Scheduler and routing engine

## Summary

Implement the route_task MCP tool and the scheduling engine that routes classified tasks to appropriate LLM backends. Build a model registry with capability metadata, backend health tracking, policy-driven routing with fallback policies, and load/queue metadata exposure. This is explicitly policy-driven, not magical — routing rules are transparent and configurable.

## Stage

planning

## Status

todo

## Depends On

- SCHED-001
- CORE-006

## Acceptance Criteria

- [ ] route_task MCP tool: accepts task description and returns routed result
- [ ] Model registry: maps routing classes to capable backends with priority
- [ ] Backend health checks integrated with routing decisions
- [ ] Policy-driven routing: configurable rules (prefer local, prefer fast, prefer capable)
- [ ] Fallback policy: if primary backend unavailable, try alternatives in priority order
- [ ] Load metadata: expose queue depth and estimated wait per backend
- [ ] Routing decision logged: task class, selected backend, alternatives, reasoning
- [ ] Dry-run mode: return routing decision without executing
- [ ] Manual override: force specific backend for a task
- [ ] Unit tests for routing logic, fallback, and health-aware routing

## Artifacts

- None yet

## Notes

- "Policy-driven, not magical" — routing rules should be inspectable and configurable
- Consider routing policies in config: [{class: "code_analysis", prefer: ["opencode-local"], fallback: ["gpt4-api"]}]
- Load balancing is round-robin or least-loaded among same-priority backends
- Queue depth tracking is best-effort — not all backends expose queue info
