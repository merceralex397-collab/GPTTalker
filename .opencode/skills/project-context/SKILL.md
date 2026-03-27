---
name: project-context
description: Load the local source-of-truth docs for this repo. Use when an OpenCode agent needs the project mission, canonical brief, workflow, ticket state, or current operating status before planning, implementing, reviewing, or handing off work.
---

# Project Context

Before reading anything else, call `skill_ping` with `skill_id: "project-context"` and `scope: "project"`.

GPTTalker is a Python 3.11+ FastAPI MCP hub with a distributed node-agent, SQLite runtime state, Qdrant-backed context retrieval, and strict fail-closed path and write-target policy enforcement over Tailscale.

For workflow resumption, treat canonical state as the source of truth and use derived restart surfaces only as a consistency check.

Read these first when resuming active work:

1. `tickets/manifest.json`
2. `.opencode/state/workflow-state.json`
3. `START-HERE.md`
4. `.opencode/state/context-snapshot.md`
5. `.opencode/state/latest-handoff.md`
6. `AGENTS.md`
7. `docs/spec/CANONICAL-BRIEF.md`
8. `docs/process/workflow.md`
9. `tickets/BOARD.md`

Current operating expectations:

- the active foreground lane is `EXEC-008` until canonical state says otherwise
- `pending_process_verification` remains meaningful even when the active ticket stays open
- `repair_follow_on` gates ordinary lifecycle work when it is incomplete
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` must agree with manifest and workflow-state, not outrank them
