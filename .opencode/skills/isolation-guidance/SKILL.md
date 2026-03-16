---
name: isolation-guidance
description: Decide when GPTTalker work should use a safer isolation lane instead of in-place editing.
---

# Isolation Guidance

Before using this guidance, call `skill_ping` with `skill_id: "isolation-guidance"` and `scope: "project"`.

## Default guidance

- use in-place edits for routine ticket work inside the generated scaffold
- use a preview directory or temporary copy for template-generation experiments
- consider a worktree or explicit isolation lane when a ticket spans many generated surfaces or risks clobbering user-authored work
- never use isolation as a reason to modify `mcp_spec_pack/`
