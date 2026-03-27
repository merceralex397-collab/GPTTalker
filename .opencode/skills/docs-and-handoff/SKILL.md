---
name: docs-and-handoff
description: Maintain START-HERE, context snapshots, and closeout artifacts for this repo. Use when a ticket changes state, a session is ending, or autonomous work needs a concise human and agent resume surface.
---

# Docs And Handoff

Before refreshing handoff artifacts, call `skill_ping` with `skill_id: "docs-and-handoff"` and `scope: "project"`.

Keep these artifacts fresh:

- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`
- `tickets/BOARD.md`
- `tickets/manifest.json`

Repo-specific handoff rules:

- treat `tickets/manifest.json` and `.opencode/state/workflow-state.json` as canonical and regenerate restart prose from them
- keep `repair_follow_on`, bootstrap status, active ticket, and `pending_process_verification` visible when they block normal execution
- do not publish a "ready for continued development" narrative while `repair_follow_on.handoff_allowed` is `false`
- keep `tickets/BOARD.md` derived from the manifest instead of hand-authoring queue state
- when the repo is verification-pending, the next action must name the blocker stage or source-level follow-up explicitly
