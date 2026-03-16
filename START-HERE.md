# GPTTalker — START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

GPTTalker is a lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment. It acts as a middleman: ChatGPT sends MCP requests, the hub enforces policy, routes work to node agents on target machines over Tailscale, and returns structured results. Built with Python + FastAPI, SQLite, Qdrant, with a Cloudflare Tunnel public edge.

## Current State

**Phase**: Initial scaffold complete — ready for implementation.

**Completed**:
- Full canonical brief with all 12 sections
- 17 OpenCode agents customized for GPTTalker (1 team leader, 3 specialized implementers, 4 reviewers/QA/docs, 3 standard pipeline agents, 6 utility agents)
- 12 project-local skills (9 customized baseline + 3 domain-specific: mcp-protocol, node-agent-patterns, context-intelligence)
- 39 implementation tickets across 11 waves (Foundation → Core → Repo Inspection → Markdown → LLM Bridge → Context → Cross-Repo → Scheduling → Observability → Edge → Polish)
- Clean repo-process-doctor audit (0 findings)
- All blocking decisions resolved

**In Progress**: Nothing — first ticket is ready to start.

**Blocked**: Nothing.

## Read In This Order

1. `README.md` — project overview, architecture diagram, MCP tools reference
2. `AGENTS.md` — coding conventions, truth hierarchy, agent team
3. `docs/spec/CANONICAL-BRIEF.md` — full project specification (12 sections)
4. `docs/process/workflow.md` — ticketed workflow process
5. `tickets/BOARD.md` — work queue overview by wave
6. `tickets/manifest.json` — machine-readable ticket state

## Current Ticket

**SETUP-001: Project skeleton and dependencies**
- Create pyproject.toml with FastAPI, uvicorn, aiosqlite, httpx, qdrant-client, pydantic, structlog, ruff, pytest
- Create src/hub/, src/node_agent/, src/shared/ directory structure
- Status: `todo` | Stage: `planning` | Dependencies: none

## Validation Status

Repo-process-doctor audit: **CLEAN** (0 findings, 0 warnings)

## Known Risks

- Embedding model choice for Qdrant indexing not yet decided (non-blocking, deferred to CTX-001)
- Qdrant deployment mode (embedded vs. standalone) TBD (non-blocking)
- Specific Cloudflare Tunnel domain/access policies TBD (non-blocking, deferred to EDGE-001)
- ChatGPT MCP protocol may evolve — reference latest OpenAI docs during implementation

## Next Action

Run `/kickoff` to begin the autonomous planning cycle for SETUP-001, or manually start planning the project skeleton and dependency setup.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
