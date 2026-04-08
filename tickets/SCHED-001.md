# SCHED-001: Task classification and routing policy

## Summary

Define how GPTTalker classifies task types and selects between approved LLM and execution backends.

## Wave

4

## Lane

scheduler

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

LLM-001, CORE-002

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Task classes are explicit
- [ ] Routing policy uses registered backend metadata
- [ ] Fallback expectations are defined

## Artifacts

- plan: .opencode/state/plans/sched-001-planning-plan.md (planning) - Planning artifact for SCHED-001: Task classification and routing policy. Defines TaskClass enum with 6 categories (coding, chat, embedding, summarize, reasoning, search), ServiceCapabilities model for backend metadata, TaskRoutingPolicy class for service selection with fallback chain, and fallback expectations for failure scenarios.
- implementation: .opencode/state/implementations/sched-001-implementation-implementation.md (implementation) - Implementation of SCHED-001: Task classification and routing policy. Created task_routing_policy.py with TaskRoutingPolicy class, TASK_CLASS_MAPPING, and fallback behavior. Added TaskClass, TaskClassification, ServiceCapabilities models to models.py. Updated llm.py, opencode.py, embedding.py with task routing support and fallback chain. Added DI provider in dependencies.py.
- review: .opencode/state/reviews/sched-001-review-review.md (review) - Approved
- qa: .opencode/state/qa/sched-001-qa-qa.md (qa) - Passed
- backlog-verification: .opencode/state/reviews/sched-001-review-backlog-verification.md (review) - Backlog verification for SCHED-001: PASS
- reverification: .opencode/state/artifacts/history/sched-001/review/2026-03-31T21-25-58-487Z-reverification.md (review) - Trust restored using SCHED-001.

## Notes


