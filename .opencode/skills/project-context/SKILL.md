---
name: project-context
description: Load the GPTTalker source-of-truth docs and architectural context. Use when an agent needs the project mission, architecture, canonical brief, or operating status before planning, implementing, reviewing, or handing off work.
---

# Project Context — GPTTalker

## What GPTTalker Is

GPTTalker is a **Python + FastAPI MCP hub** that lets ChatGPT interact with a multi-machine dev environment. It exposes MCP tools that ChatGPT invokes to inspect repos, deliver markdown, bridge LLM calls, query project context, perform cross-repo intelligence, route distributed operations, and observe task history — all across machines connected via Tailscale.

## Architecture Overview

```
ChatGPT ─→ Cloudflare Tunnel ─→ Hub Server (src/hub/)
                                      │
                              Tailscale mesh network
                                      │
                    ┌─────────────────┼─────────────────┐
                Node Agent A    Node Agent B    Node Agent N
              (src/node_agent/) (src/node_agent/) ...
                    │                │                │
              Local machine    Local machine    Local machine
```

- **Hub server** (`src/hub/`): Central FastAPI service that receives MCP tool calls from ChatGPT, validates inputs against registries, routes operations to the correct node agent, and assembles responses.
- **Node agents** (`src/node_agent/`): Lightweight FastAPI services running on each managed machine. They execute local operations (repo inspection, file writes, LLM calls) and report results back to the hub.
- **Tailscale**: Private mesh network connecting hub to all node agents.
- **Cloudflare Tunnel**: HTTPS edge providing a stable public endpoint for ChatGPT to reach the hub.

## Key Technology Decisions

| Concern | Choice | Rationale |
|---|---|---|
| Vector storage | Qdrant | Fast semantic search across repos |
| Structured data | SQLite (aiosqlite) | Lightweight, zero-ops persistence |
| HTTPS edge | Cloudflare Tunnel | Stable public URL without port-forwarding |
| Inter-machine networking | Tailscale | Private mesh, zero-config WireGuard |
| Node architecture | Node-agent pattern | Each machine runs its own agent for local ops |

## MCP Tools Provided

The hub exposes these tool categories to ChatGPT:

1. **Repo inspection** — tree, file read, search, git status (routed to node agents)
2. **Markdown delivery** — write files to target repos (routed to node agents)
3. **LLM bridge** — forward prompts to local LLMs on node machines
4. **Project context** — retrieve indexed context bundles from Qdrant
5. **Cross-repo intelligence** — semantic search across all indexed repos
6. **Distributed routing** — resolve which node agent owns a given repo/target
7. **Observability** — task history, operation logs, health checks

## Canonical Docs — Read These First

1. `docs/spec/CANONICAL-BRIEF.md` — full project specification
2. `AGENTS.md` — agent team definitions and responsibilities
3. `README.md` — project overview and setup
4. `docs/process/workflow.md` — development workflow
5. `tickets/manifest.json` — current ticket state
6. `tickets/BOARD.md` — ticket board overview
