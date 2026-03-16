---
name: docs-and-handoff
description: Keep GPTTalker’s README, process docs, ticket views, and START-HERE surface aligned with canonical state.
---

# Docs and Handoff

Before using this guidance, call `skill_ping` with `skill_id: "docs-and-handoff"` and `scope: "project"`.

## Primary surfaces

- `README.md` for project overview and honest repo state
- `docs/process/` for workflow, tooling, models, and agent catalog
- `tickets/BOARD.md` as the derived human view
- `START-HERE.md` as the restart surface

## Rules

- regenerate derived views from canonical state instead of hand-waving their contents
- keep `START-HERE.md` concise and specific
- preserve `mcp_spec_pack/` exactly as reference material
- when the repo state changes materially, update handoff and provenance together
