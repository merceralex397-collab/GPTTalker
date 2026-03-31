---
name: workflow-observability
description: Inspect GPTTalker's bootstrap, process-version, pivot, and repair-follow-on state to explain what the managed workflow is actually doing.
---

# Workflow Observability

## Read In Order

1. `.opencode/meta/bootstrap-provenance.json`
2. `.opencode/meta/repair-follow-on-state.json`
3. `.opencode/meta/pivot-state.json`
4. `.opencode/state/invocation-log.jsonl` if it exists
5. `.opencode/state/last-ticket-event.json` if it exists
6. `.opencode/state/workflow-state.json`
7. `tickets/manifest.json`

## Return Sections

1. `Bootstrap`
2. `Process Changes`
3. `Repair Follow-On`
4. `Pivot`
5. `Observed Usage`
6. `Missing Or Never-Seen Surfaces`
7. `Workflow Drift Risks`
8. `Next Fix`

## Repo-Specific Notes

- Treat `.opencode/meta/bootstrap-provenance.json` as the canonical process-contract record.
- Treat `.opencode/meta/repair-follow-on-state.json` as the canonical per-cycle repair-follow-on record.
- If `pending_process_verification` is true, say so explicitly and name the affected follow-up lane.
- If no invocation log exists yet, say `no invocation data yet`.
