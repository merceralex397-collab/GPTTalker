---
name: node-agent-patterns
description: Hold GPTTalker’s node-agent design rules for local execution, Tailscale transport, and bounded subprocess work.
---

# Node Agent Patterns

Use this skill for tickets that touch the per-machine agent.

## Rules

- keep the node agent lightweight and fast to start
- prefer `asyncio.create_subprocess_exec` for local `git` and `rg` calls with explicit timeouts
- validate repo and write-target paths before any local operation
- use `httpx.AsyncClient` for local LLM forwarding and hub callbacks
- expose health and readiness in structured JSON
