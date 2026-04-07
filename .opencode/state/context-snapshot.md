# GPTTalker — Context Snapshot

Generated: 2026-04-07 (repair cycle 2026-04-07T22:18:12Z)

## Project

GPTTalker — MCP hub for safe ChatGPT access to a multi-machine dev environment.
Stack: Python 3.11+ / FastAPI / aiosqlite / Qdrant / httpx / Tailscale / Cloudflare Tunnel
Model: minimax-coding-plan/MiniMax-M2.7

## Work State

- 65/67 tickets done
- 2 tickets todo: REMED-001 (hub import fix), REMED-002 (advisory)
- Active ticket: REMED-001 (fix RelationshipService annotation NameError in src/hub/dependencies.py)

## Repair State

Managed-surface overhaul complete (cycle 2026-04-07T22:18:12Z):
- All 8 agent drift findings resolved
- stack-standards/SKILL.md populated (project-specific)
- Remediation tickets created: REMED-001 (EXEC001), REMED-002 (REF-003 advisory)
- Completion artifacts: .opencode/state/artifacts/history/repair/*-completion.md

Known issue: run_managed_repair.py always re-writes stack-standards/SKILL.md from template.
Do not run the repair runner again; both follow-on stages are complete.

## Pending

- REMED-001: one-line fix in src/hub/dependencies.py to use string annotation
- REMED-002: advisory only, no action needed

## Risk

- Hub cannot import until REMED-001 is fixed
- REF-003 (zod) is a false positive
