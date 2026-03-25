---
name: model-operating-profile
description: Keep GPTTalker's repo-local model choices, evidence standards, and prompt-shaping rules explicit. Use when editing agent prompts, workflow guidance, or managed model metadata.
---

# Model Operating Profile

Before applying these rules, call `skill_ping` with `skill_id: "model-operating-profile"` and `scope: "project"`.

Current repo choice:

- provider: `minimax-coding-plan`
- planner and reviewers: `minimax-coding-plan/MiniMax-M2.7`
- implementers: `minimax-coding-plan/MiniMax-M2.7`
- utilities, QA, and docs: `minimax-coding-plan/MiniMax-M2.7`

Operating rules:

- treat the current MiniMax assignment as an intentional repo-local choice documented in `docs/spec/CANONICAL-BRIEF.md`; do not swap models during normal ticket work
- prefer short, explicitly structured outputs with concrete next actions
- stage transitions require artifact or command evidence, not label-based inference
- when validation is required, include raw command output rather than summaries
- return a blocker instead of guessing when requirements, approval state, or proof artifacts are missing
- use repo-local skills and workflow tools to hold stable procedure; keep prompt prose short

When to escalate:

- if a human wants to move off the current MiniMax profile, update `docs/spec/CANONICAL-BRIEF.md`, `docs/process/model-matrix.md`, `START-HERE.md`, provenance, and agent frontmatter together
- if package defaults conflict with this repo-local choice, preserve the documented repo decision and record the mismatch in repair notes instead of silently changing models
