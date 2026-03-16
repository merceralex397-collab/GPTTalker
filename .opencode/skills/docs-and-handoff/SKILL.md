---
name: docs-and-handoff
description: Maintain GPTTalker's handoff artifacts, API documentation, architecture notes, and deployment guides. Use when a ticket changes state, a session is ending, or docs need updating after implementation changes.
---

# Docs And Handoff — GPTTalker

## Handoff Artifacts — Keep Fresh

These artifacts must be updated whenever ticket state changes or a session ends:

- `START-HERE.md` — project entry point for humans and agents
- `.opencode/state/context-snapshot.md` — current session context for agent resume
- `tickets/BOARD.md` — human-readable board view
- `tickets/manifest.json` — machine-readable ticket index

## API Documentation

- All MCP tools must be documented with their request/response schemas
- Document tool categories: repo inspection, markdown delivery, LLM bridge, project context, cross-repo intelligence, distributed routing, observability
- Keep tool docs in sync with actual handler implementations in `src/hub/tools/`
- When an MCP tool is added or its contract changes, update `docs/spec/CANONICAL-BRIEF.md`

## Architecture Notes

- Architecture documentation lives in `docs/`
- Keep architecture diagrams and descriptions current when structural changes occur
- Document any new registries, routing rules, or node-agent capabilities
- When the hub-to-node communication protocol changes, update both hub and node-agent docs

## Deployment Guide

The deployment guide must cover:

- **Tailscale setup** — how to join machines to the tailnet, assign stable IPs, configure ACLs
- **Cloudflare Tunnel setup** — how to create and configure the tunnel for the hub's public HTTPS endpoint
- **Hub server deployment** — how to start the hub, configure registries, set environment variables
- **Node agent deployment** — how to deploy and register a new node agent on a managed machine
- **Health verification** — how to confirm all components are connected and healthy
