---
name: workflow-observability
description: Inspect GPTTalker’s bootstrap provenance, workflow state, invocation logs, and migration state when auditing repo health.
---

# Workflow Observability

Before using this guidance, call `skill_ping` with `skill_id: "workflow-observability"` and `scope: "project"`.

## Inspect these first

- `.opencode/meta/bootstrap-provenance.json`
- `.opencode/state/workflow-state.json`
- `.opencode/state/artifacts/registry.json`
- `.opencode/state/invocation-log.jsonl` when it exists
- `.opencode/state/last-ticket-event.json` when it exists

## Use cases

- confirm process-version and retrofit history
- determine whether post-migration verification is still active
- identify unused or never-seen tools, agents, or skills
- confirm the active ticket and most recent state transitions
