---
name: repo-navigation
description: Navigate GPTTalker’s generated workflow layer and preserved source pack without confusing generated surfaces for immutable source material.
---

# Repo Navigation

Before using this guidance, call `skill_ping` with `skill_id: "repo-navigation"` and `scope: "project"`.

## Key directories

- `mcp_spec_pack/` — preserved reference pack; read-only source material
- `docs/spec/` — normalized project brief and durable project definition
- `docs/process/` — workflow, tooling, model, and agent-process docs
- `tickets/` — backlog manifest, board, and detailed ticket views
- `.opencode/agents/` — repo-local agent prompts
- `.opencode/tools/` — workflow and ticket tools
- `.opencode/skills/` — local procedure packs
- `.opencode/state/` — workflow state and artifact bodies

## Navigation rules

- treat `mcp_spec_pack/` as evidence, not a generated surface
- prefer `tickets/manifest.json` over `tickets/BOARD.md` when machine state matters
- prefer `.opencode/meta/bootstrap-provenance.json` over memory when deciding whether a surface was replaced or repaired
- check `.opencode/state/workflow-state.json` before assuming the active ticket or process-verification window

## Common queries

- active ticket and artifact summary: `ticket_lookup`
- backlog ownership and dependencies: `tickets/manifest.json`
- process contract and retrofit history: `.opencode/meta/bootstrap-provenance.json`
- source-pack rationale for a feature: search `mcp_spec_pack/`
