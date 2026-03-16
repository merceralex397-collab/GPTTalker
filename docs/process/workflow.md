# Workflow

The default workflow for `GPTTalker` is:

1. spec intake
2. ticket selection
3. planning
4. plan review
5. implementation
6. code review
7. security review when relevant
8. QA
9. handoff and closeout

Rules:

- do not skip plan review
- do not start implementation without an approved plan
- do not close a ticket until artifacts and state files are updated
- keep the autonomous flow internal to agents, tools, plugins, and local skills
- keep ticket `status` coarse and queue-oriented: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`
- keep plan approval in `.opencode/state/workflow-state.json`, not in ticket status
- treat `tickets/BOARD.md` as a derived human view, not an authoritative workflow surface
- write stage artifact bodies with `artifact_write` and then register them with `artifact_register`
- require a registered stage artifact before advancing to the next stage

## Canonical ownership

- immutable source material lives in `mcp_spec_pack/`
- durable project facts live in `docs/spec/CANONICAL-BRIEF.md`
- machine queue state and artifact metadata live in `tickets/manifest.json`
- transient approval, current-stage state, and process-version state live in `.opencode/state/workflow-state.json`
- artifact bodies live in the stage-specific directories under `.opencode/state/`
- cross-stage artifact metadata lives in `.opencode/state/artifacts/registry.json`
- restart guidance lives in `START-HERE.md` and should be regenerated from canonical state

## Stage proof

- before plan review: a `planning` artifact must exist
- before implementation: `approved_plan` must be `true`
- before code review: an `implementation` artifact must exist
- before QA: a review artifact must exist
- before closeout: a `qa` artifact must exist

## Parallel lanes

- keep each individual ticket sequential through the stage flow
- advance multiple tickets in parallel only when each ticket is marked `parallel_safe: true`, `overlap_risk: low`, has no unresolved dependency edge, and does not require overlapping write-capable work in the same lane
- prefer one visible team leader coordinating explicit parallel lanes over adding multiple managers

## Process migration

- record scaffold and retrofit history in `.opencode/meta/bootstrap-provenance.json`
- mirror the active process contract in `.opencode/state/workflow-state.json`
- only open a post-migration verification window when older completed work is still being trusted after a process change
- route those checks through `backlog-verifier` and guarded follow-up creation through `ticket_create`
