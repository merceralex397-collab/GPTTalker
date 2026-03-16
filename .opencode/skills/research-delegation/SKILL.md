---
name: research-delegation
description: Gather GPTTalker evidence through read-only utility agents and preserve findings without mutating repo-tracked files.
---

# Research Delegation

Before using this guidance, call `skill_ping` with `skill_id: "research-delegation"` and `scope: "project"`.

## Preferred lanes

- `utility-explore` for repo evidence gathering
- `utility-web-research` for external docs
- `utility-github-research` for GitHub references and prior art
- `utility-summarize` for large-output compression

## Rules

- keep delegated work read-only unless the stage explicitly writes an artifact
- cite `mcp_spec_pack/` when the research output relies on preserved source material
- persist durable findings as artifacts, not ad hoc ticket edits
