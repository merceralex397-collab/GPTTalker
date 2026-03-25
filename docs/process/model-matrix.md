# Model Matrix

Default stack label: `framework-agnostic`

These values should come from an explicit user choice during scaffold generation, not from a hidden generator default.

- provider: `minimax-coding-plan`
- team lead / planner / reviewers: `minimax-coding-plan/MiniMax-M2.7`
- implementer: `minimax-coding-plan/MiniMax-M2.7`
- utilities, docs, and QA helpers: `minimax-coding-plan/MiniMax-M2.7`
- operating profile: `Specific-instruction evidence-first profile`
- repo-local profile skill: `.opencode/skills/model-operating-profile/SKILL.md`

Profile guidance:

- `Apply explicit, example-shaped, bounded instructions for the selected downstream models. Prefer direct evidence and concrete task framing over broad summaries.`

If the project chooses a different runtime model strategy later, update the canonical brief, this file, and `.opencode/skills/model-operating-profile/SKILL.md` together.
