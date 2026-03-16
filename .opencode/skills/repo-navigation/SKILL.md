---
name: repo-navigation
description: Navigate GPTTalker's source tree, docs, tickets, and OpenCode surfaces. Use when an agent needs to locate hub code, node-agent code, tool handlers, registries, context pipeline, or process docs without scanning the entire repository.
---

# Repo Navigation — GPTTalker

## Source Code

### Hub Server — `src/hub/`

| Path | Contents |
|---|---|
| `src/hub/` | FastAPI hub server entry point, MCP tool handlers, policy engine, config |
| `src/hub/tools/` | MCP tool implementations (one module per tool category) |
| `src/hub/registry/` | Node registry, repo registry, write-target registry, LLM service registry |
| `src/hub/context/` | Qdrant integration, indexing pipeline, context bundle assembly |
| `src/hub/llm/` | LLM bridge, model adapters, request scheduler |
| `src/hub/observability/` | Task history, structured logging, trace ID management |

### Node Agent — `src/node_agent/`

| Path | Contents |
|---|---|
| `src/node_agent/` | Node agent FastAPI service entry point, health checks, capability advertisement |
| `src/node_agent/inspection/` | Repo tree walker, file reader, code search, git status |
| `src/node_agent/delivery/` | Markdown file writer, safe-write logic |
| `src/node_agent/llm/` | Local LLM service communication (forward prompts to local models) |

### Shared — `src/shared/`

| Path | Contents |
|---|---|
| `src/shared/` | Shared Pydantic models, utility functions, common types used by both hub and node agent |

## Documentation

| Path | Contents |
|---|---|
| `README.md` | Project overview, quick start |
| `AGENTS.md` | OpenCode agent team definitions |
| `docs/spec/` | Canonical brief, architecture spec |
| `docs/process/` | Workflow, review checklists |
| `docs/` | All project documentation |

## Tickets & Process

| Path | Contents |
|---|---|
| `tickets/` | Work queue — individual ticket files |
| `tickets/manifest.json` | Machine-readable ticket index |
| `tickets/BOARD.md` | Human-readable board view |

## OpenCode Surfaces

| Path | Contents |
|---|---|
| `.opencode/` | Agent team root |
| `.opencode/agents/` | Agent definitions |
| `.opencode/skills/` | Skill definitions (you are here) |
| `.opencode/tools/` | Custom tool definitions |
| `.opencode/commands/` | Custom commands |
| `.opencode/plugins/` | Plugin configs |
| `.opencode/state/` | Runtime state (workflow, invocation log) |
| `.opencode/meta/` | Bootstrap provenance |

## Navigation Tips

- **Looking for an MCP tool handler?** → `src/hub/tools/`
- **Looking for how the hub finds a node agent?** → `src/hub/registry/`
- **Looking for Qdrant/embedding logic?** → `src/hub/context/`
- **Looking for what runs on a managed machine?** → `src/node_agent/`
- **Looking for request/response models?** → `src/shared/`
- **Looking for the full spec?** → `docs/spec/CANONICAL-BRIEF.md`
