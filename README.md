# GPTTalker

GPTTalker is a **scaffolded implementation repo** for a lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment.

The repo currently contains the operating layer, canonical brief, ticket backlog, and project-local OpenCode team needed to build the system. It does **not** yet contain the runtime implementation under `src/`; the first execution wave in `tickets/manifest.json` is the handoff point for that work.

## Current status

- Source material is preserved in `mcp_spec_pack/`
- The repo has been fully re-scaffolded from the updated Scafforge templates
- The OpenCode operating layer, backlog, local skills, and handoff surface were regenerated for GPTTalker
- `SETUP-001` is the active ready ticket for implementation kickoff

## Planned system

The target system is a Python + FastAPI MCP hub that:

- exposes policy-controlled MCP tools to ChatGPT
- routes repo inspection, markdown delivery, and LLM calls to approved nodes over Tailscale
- stores structured registry and history state in SQLite
- stores semantic project context in Qdrant
- exposes a public HTTPS edge through Cloudflare Tunnel
- keeps all access fail-closed with no unrestricted shell exposure

## Repository layout

- `mcp_spec_pack/` — immutable reference material that existed before repo generation
- `docs/spec/CANONICAL-BRIEF.md` — normalized project source of truth
- `docs/process/` — workflow, tooling, model, and agent-process docs for the generated operating layer
- `tickets/` — machine-readable backlog, human board, and per-ticket detail files
- `.opencode/` — project-local agents, tools, plugins, commands, skills, state, and provenance
- `START-HERE.md` — restart surface for the next session or machine

## How to work in this repo

1. Read `START-HERE.md`
2. Read `AGENTS.md`
3. Read `docs/spec/CANONICAL-BRIEF.md`
4. Read `docs/process/workflow.md`
5. Read `tickets/manifest.json`
6. Start with the active ticket and follow the ticketed stage flow

## Source material and truth

The original source pack in `mcp_spec_pack/` is intentionally preserved and should remain untouched. If generated docs ever conflict with the preserved source pack, regenerate or repair the generated layer rather than editing the source pack.
