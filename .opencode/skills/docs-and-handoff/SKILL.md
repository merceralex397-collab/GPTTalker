---
name: docs-and-handoff
description: Keep GPTTalker's derived restart surfaces aligned with manifest, workflow, pivot, and repair-follow-on truth.
---

# Docs And Handoff

## Primary Derived Surfaces

- `START-HERE.md`
- `.opencode/state/context-snapshot.md`
- `.opencode/state/latest-handoff.md`
- `tickets/BOARD.md`

## Canonical Inputs

- `tickets/manifest.json`
- `.opencode/state/workflow-state.json`
- `.opencode/meta/pivot-state.json`
- `.opencode/meta/repair-follow-on-state.json`
- `docs/spec/CANONICAL-BRIEF.md`

## Repo-Specific Rules

- Restart surfaces are derived views. They must not invent state that is missing from manifest or workflow state.
- If repair follow-on is complete, restart surfaces must stop saying `managed_blocked`.
- If pivot follow-up remains open, keep that risk explicit until the edge and lineage tickets actually close.
- When the active ticket changes, refresh the restart surfaces so weaker models do not resume from a closed ticket.
- Keep next-action guidance concrete: name the next ticket or blocker, not a generic summary.
