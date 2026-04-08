---
name: repo-navigation
description: Navigate GPTTalker's code, tests, workflow surfaces, and restart documents without re-scanning the whole repository.
---

# Repo Navigation

## Top-Level Areas

- `src/hub/`: FastAPI hub app, MCP transport, policy engine, tool handlers, service clients, and ngrok edge integration.
- `src/node_agent/`: per-machine service, bounded executor, health routes, and local operation endpoints.
- `src/shared/`: config, logging, context helpers, database layer, schemas, tables, and repositories shared by hub and node agent.
- `tests/hub/`: transport, contract, security, routing, and tunnel-manager coverage.
- `tests/node_agent/`: bounded executor and repo-operation behavior.
- `tests/shared/`: shared logging and runtime helpers.
- `docs/spec/`: canonical project definition.
- `docs/process/`: workflow, model, git, and agent contract docs.
- `tickets/`: canonical machine backlog plus human ticket docs.
- `.opencode/`: agents, skills, commands, tools, workflow state, artifact history, and restart surfaces.
- `diagnosis/`: read-only audit and repair evidence packs.

## Common Lookups

- Hub public edge: `src/hub/config.py`, `src/hub/lifespan.py`, `src/hub/services/tunnel_manager.py`, `tests/hub/test_tunnel_manager.py`
- Policy and path safety: `src/hub/policy/`, `src/node_agent/executor.py`, `tests/hub/test_security.py`
- MCP tool contracts: `src/hub/tools/`, `src/hub/transport/`, `tests/hub/test_contracts.py`, `tests/hub/test_transport.py`
- Shared storage: `src/shared/database.py`, `src/shared/migrations.py`, `src/shared/repositories/`
- Context and Qdrant: `src/hub/services/qdrant_client.py`, `src/hub/services/indexing_pipeline.py`, `src/hub/tools/context.py`, `src/hub/tools/cross_repo.py`

## Common Queries

- Find repo code quickly: `rg --files src tests docs tickets .opencode`
- Find a tool handler: `rg -n "def .*handler|async def .*handler" src/hub/tools`
- Find workflow drift: `rg -n "repair_follow_on|pending_process_verification|pivot" .opencode START-HERE.md tickets`
- Find lingering Cloudflare references during ngrok work: `rg -n "Cloudflare|cloudflared" src docs tests .opencode`

## Ticket Surfaces

- Ticket machine truth: `tickets/manifest.json`
- Ticket human doc: `tickets/<ID>.md`
- Board: `tickets/BOARD.md`
- Artifact bodies: `.opencode/state/{plans,implementations,reviews,qa,artifacts/history}/`
