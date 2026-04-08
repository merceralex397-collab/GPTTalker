---
name: project-context
description: Load GPTTalker's canonical truth, current workflow state, and open follow-up lanes before planning, implementation, review, or handoff work.
---

# Project Context

## What This Repo Is

GPTTalker is a Python 3.11+ FastAPI MCP hub plus per-machine node agent. The hub enforces policy, routes bounded work over Tailscale, stores structured state in SQLite, stores semantic context in Qdrant, and now treats ngrok as the canonical public edge.

## Read Order

1. `tickets/manifest.json`
2. `.opencode/state/workflow-state.json`
3. `START-HERE.md`
4. `.opencode/state/context-snapshot.md`
5. `.opencode/state/latest-handoff.md`
6. `AGENTS.md`
7. `docs/spec/CANONICAL-BRIEF.md`
8. `mcp_spec_pack/00-overview/00_project_brief.md`
9. `docs/process/workflow.md`
10. `docs/process/agent-catalog.md`
11. `docs/process/model-matrix.md`
12. `docs/process/git-capability.md`
13. `tickets/README.md`
14. `tickets/BOARD.md`

## Canonical Owners

- Durable project decisions: `docs/spec/CANONICAL-BRIEF.md`
- Machine queue truth: `tickets/manifest.json`
- Active stage and approval state: `.opencode/state/workflow-state.json`
- Repair-cycle truth: `.opencode/meta/repair-follow-on-state.json`
- Pivot truth: `.opencode/meta/pivot-state.json`
- Restart surfaces: `START-HERE.md`, `.opencode/state/context-snapshot.md`, `.opencode/state/latest-handoff.md`

## Current Operating Notes

- The repo is on process version `7`.
- `pending_process_verification` can still be true even when the next active lane is ordinary ticket work; do not treat restart prose as proof.
- The current architecture truth is `ngrok` for the public HTTPS edge and `Tailscale` for internal transport.
- Source-layer follow-up currently exists alongside pivot follow-up. Check open tickets before assuming the active lane is still a closed hardening ticket.

## Fast Checks

- Use `tickets/manifest.json` to find the real foreground ticket and any open follow-up graph.
- Use `.opencode/state/workflow-state.json` to confirm bootstrap readiness, plan approval, and repair-follow-on outcome.
- Use `docs/spec/CANONICAL-BRIEF.md` before changing stack, security, or edge assumptions.
