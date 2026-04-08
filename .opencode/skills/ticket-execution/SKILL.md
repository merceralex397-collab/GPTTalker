---
name: ticket-execution
description: Follow GPTTalker's exact ticket lifecycle, bootstrap gate, artifact ownership model, and blocker behavior.
---

# Ticket Execution

## Canonical Order

`planning -> plan_review -> implementation -> review -> qa -> smoke-test -> closeout`

Queue status stays coarse: `todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`.

## Required Routing Rules

- Start with `ticket_lookup`.
- Read `ticket_lookup.transition_guidance` before any `ticket_update`.
- If `ticket_lookup.bootstrap.status` is not `ready`, the next legal action is `environment_bootstrap`, then a fresh `ticket_lookup`.
- If bootstrap still is not `ready`, return a blocker. Do not improvise package-manager commands or raw environment workarounds.
- If `repair_follow_on.outcome` is `managed_blocked`, stop ordinary lifecycle routing and surface that blocker first.
- If the same lifecycle error happens twice, stop and return a blocker instead of probing alternate stage or status values.
- Slash commands are human entrypoints, not autonomous workflow tools.

## Artifact Ownership

- Planner owns `planning`
- Implementer owns `implementation`
- Reviewer or security reviewer owns `review`
- QA owns `qa`
- `smoke_test` is the only legal producer of `smoke-test`

## Stage Rules

- `planning`
  - leave a registered planning artifact before moving on
- `plan_review`
  - approval lives in `.opencode/state/workflow-state.json`
  - do not combine plan approval with the move to implementation
- `implementation`
  - leave runnable evidence such as import, compile, lint, or test output
- `review`
  - findings first, then approval or blocker
- `qa`
  - include raw command output or an explicit environment blocker
- `smoke-test`
  - use the canonical smoke command from the ticket acceptance when one exists
- `closeout`
  - requires a current passing smoke-test artifact

## Blocker Rules

- If execution or validation cannot run, return a blocker instead of manufacturing PASS evidence.
- Missing host prerequisites such as `uv`, `pytest`, `rg`, git identity, or required service binaries must be classified explicitly.
- If proof exists only in prose and not in a canonical artifact, treat the stage as incomplete.

## Parallel Rules

- Keep each ticket sequential through its own stages.
- Only parallelize when `parallel_safe` is true, `overlap_risk` is low, dependencies are already satisfied, and write ownership does not overlap.
