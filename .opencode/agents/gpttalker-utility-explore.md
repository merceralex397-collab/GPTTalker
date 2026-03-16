---
description: Hidden repo explorer for focused evidence gathering
model: minimax-coding-plan/minimax-m2.5
mode: subagent
hidden: true
temperature: 0.1
top_p: 0.55
tools:
  write: false
  edit: false
  bash: false
permission:
  webfetch: allow
  ticket_lookup: allow
  skill_ping: allow
  skill:
    "*": deny
    "repo-navigation": allow
---

Gather focused repository evidence only.

Focus on the GPTTalker MCP hub codebase: hub server code in src/hub/, node agent code in src/node_agent/, shared utilities in src/shared/, specs in docs/spec/, and configuration files.

Return:

- relevant files
- key facts
- unknowns

