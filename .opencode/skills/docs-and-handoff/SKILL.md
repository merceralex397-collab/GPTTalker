---
name: docs-and-handoff
description: Maintain START-HERE, context snapshots, and closeout artifacts for this repo. Use when a ticket changes state, a session is ending, or autonomous work needs a concise human and agent resume surface.
---

# Docs And Handoff

Before refreshing handoff artifacts, call `skill_ping` with `skill_id: "docs-and-handoff"` and `scope: "project"`.

Keep these artifacts fresh:

- `START-HERE.md`
- `.opencode/state/latest-handoff.md`
- `.opencode/state/context-snapshot.md`
- `tickets/BOARD.md`
- `tickets/manifest.json`

Rules:

- treat `START-HERE.md`, `.opencode/state/latest-handoff.md`, and `.opencode/state/context-snapshot.md` as derived restart surfaces that must agree with `tickets/manifest.json` and `.opencode/state/workflow-state.json`
- do not publish “bootstrap ready”, “workflow repaired”, or dependency-unblocked claims when canonical workflow state still says otherwise
