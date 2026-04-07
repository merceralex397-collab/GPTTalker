# GPTTalker Agent Delegation

This document is derived from the repo-local agent team in `.opencode/agents/`.

## Restart Procedure

1. Read `START-HERE.md`.
2. Run `ticket_lookup`.
3. Treat `tickets/manifest.json` and `.opencode/state/workflow-state.json` as canonical.
4. Resume only from `transition_guidance` and current repair/bootstrap state.

## Team

- `gpttalker-team-leader`: visible coordinator. Owns ticket routing, lifecycle enforcement, bootstrap-first gating, smoke-test execution, and lease control. Does not author planning, implementation, review, or QA artifacts.
- `gpttalker-planner`: produces a single-ticket implementation plan.
- `gpttalker-plan-review`: validates plan completeness and feasibility before implementation.
- `gpttalker-lane-executor`: default bounded write-capable worker when parallel isolated work is safe.
- `gpttalker-implementer`: shared-runtime and cross-cutting workflow/code owner.
- `gpttalker-implementer-hub`: FastAPI hub, registries, policy, and edge ownership.
- `gpttalker-implementer-node-agent`: node-agent and local executor ownership.
- `gpttalker-implementer-context`: Qdrant, indexing, context, and cross-repo routing ownership.
- `gpttalker-reviewer-code`: correctness and regression review.
- `gpttalker-reviewer-security`: trust boundary, redaction, and policy review.
- `gpttalker-tester-qa`: command-backed QA validation.
- `gpttalker-docs-handoff`: restart surfaces and closeout docs.
- `gpttalker-backlog-verifier`: historical trust restoration after process changes.
- `gpttalker-ticket-creator`: guarded follow-up ticket creation from current evidence.

## Stage Flow

- `planning`: team leader delegates to `gpttalker-planner`.
- `plan_review`: team leader delegates to `gpttalker-plan-review`.
- `implementation`: team leader routes to the correct implementer or `gpttalker-lane-executor`.
- `review`: team leader routes to `gpttalker-reviewer-code` and `gpttalker-reviewer-security` when relevant.
- `qa`: team leader routes to `gpttalker-tester-qa`.
- `smoke-test`: team leader runs `smoke_test` directly.
- `closeout`: team leader routes restart-surface refresh to `gpttalker-docs-handoff`.

## Escalation Rules

- If bootstrap is not `ready`, run `environment_bootstrap` before normal lifecycle work.
- If `repair_follow_on.outcome` is `managed_blocked`, stop ordinary ticket routing and complete the required repair follow-on stage first.
- If `ticket_lookup.transition_guidance.recovery_action` is present, that recovery path is the next legal move after failure or contradiction.
- If the same ticket-tool rejection happens twice, stop and return a blocker instead of stage probing.
- Read-only agents return findings or blockers only; they never mutate repo files.
