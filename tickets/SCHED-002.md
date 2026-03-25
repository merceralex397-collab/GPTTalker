# SCHED-002: Distributed scheduler, node selection, and fallback

## Summary

Implement the distributed scheduler that considers task type, node health, service availability, and fallback rules.

## Wave

4

## Lane

scheduler

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

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

SCHED-001, CORE-004, LLM-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Scheduler inputs are explicit
- [ ] Node and backend health affect routing decisions
- [ ] Fallback behavior is defined and bounded

## Artifacts

- plan: .opencode/state/plans/sched-002-planning-plan.md (planning) - Planning artifact for SCHED-002: Distributed scheduler, node selection, and fallback. Defines SchedulerInput model with all decision factors, DistributedScheduler class extending TaskRoutingPolicy with node-level awareness, health-aware filtering, latency-aware selection, and bounded fallback behavior.
- implementation: .opencode/state/implementations/sched-002-implementation-implementation.md (implementation) - Implementation of SCHED-002: Created distributed scheduler with node-aware service selection, health filtering, latency-aware selection, and bounded fallback chain. Added SchedulerInput, SchedulerResult, NodeHealthInfo, and ServiceNodePair models to models.py. Created DistributedScheduler class in new distributed_scheduler.py file. Updated dependencies.py with DI provider. Integrated distributed scheduler into llm.py, opencode.py, and embedding.py tools.
- review: .opencode/state/reviews/sched-002-review-review.md (review) - Approved
- qa: .opencode/state/qa/sched-002-qa-qa.md (qa) - Passed
- backlog-verification: .opencode/state/reviews/sched-002-review-backlog-verification.md (review) - Backlog verification for SCHED-002: PASS

## Notes


