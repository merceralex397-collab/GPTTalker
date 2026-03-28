# GPTTalker — Junie Project Guidelines

## Project Overview

GPTTalker is a lightweight **MCP (Model Context Protocol) hub** built with Python 3.11+ and FastAPI. It lets ChatGPT safely interact with a multi-machine development environment. The hub enforces policy, routes work to the correct machine over **Tailscale**, and returns structured results. A public HTTPS edge is provided via **Cloudflare Tunnel**.

### Key Capabilities

- **Repo inspection**: file trees, file reading, text/symbol search, git status
- **Controlled markdown delivery**: atomic writes to approved write roots
- **LLM bridging**: route prompts to approved local models, OpenCode agents, and embedding services
- **Persistent project context**: per-repo summaries, semantic vector search via Qdrant
- **Cross-repo intelligence**: global search, relationship metadata, dependency/architecture graphs
- **Distributed LLM routing**: multi-machine model routing with task classification and health checks
- **Observability**: task history, generated document history, issue timelines, audit logs
- **Node-agent architecture**: lightweight agent on each managed machine, hub routes over Tailscale

### Security Model

- **Default deny**: unknown nodes, repos, write targets, and LLM aliases are rejected
- **Fail closed**: validation or policy failures return structured errors
- **No unrestricted shell access**: only bounded tool handlers are exposed
- **Path normalization**: reject `..`, symlink escapes, and absolute user-supplied paths
- **Atomic writes only**: write-to-temp then rename
- **Redacted logging**: no secrets, tokens, passwords, or raw file contents in logs

## Repository Layout

```
src/
├── hub/                    # FastAPI MCP hub server
│   ├── policy/             # Policy engine, distributed scheduler, task routing
│   ├── services/           # Node health, service layer
│   ├── tool_routing/       # Tool router, routing errors
│   ├── tools/              # MCP tool handlers (inspection, write, LLM, context, etc.)
│   └── transport/          # Cloudflare tunnel, transport layer
├── node_agent/             # Per-machine node agent service
│   └── routes/             # Node agent HTTP routes
└── shared/                 # Shared schemas, repositories, config, exceptions
    └── repositories/       # Database repositories, relationship management

tests/                      # pytest test suite
├── hub/                    # Hub tests (transport, tools, policy)
├── node_agent/             # Node agent tests (executor)
└── shared/                 # Shared module tests

docs/
├── spec/                   # CANONICAL-BRIEF.md — canonical project definition
├── process/                # workflow.md, agent catalog, model matrix
└── ops/                    # Operational documentation

tickets/                    # Scafforge-managed ticket backlog
mcp_spec_pack/              # Immutable pre-generation source pack (do not rewrite)
scripts/                    # Validation, test, and lint runner scripts
diagnosis/                  # Diagnosis reports from overseer reviews
```

## Tech Stack

| Component | Technology |
|---|---|
| Runtime | Python 3.11+, FastAPI, uvicorn |
| Database | SQLite via aiosqlite (async only) |
| Vector store | Qdrant for semantic search |
| HTTP client | httpx (async, explicit timeouts) |
| Data models | Pydantic v2 |
| Internal network | Tailscale |
| Public edge | Cloudflare Tunnel |
| Package manager | uv |
| Linting | ruff |
| Testing | pytest, pytest-asyncio |

## Coding Conventions

- **Type hints everywhere**: function signatures, return types, and non-obvious variables
- Prefer `str | None` over `Optional[str]`
- **Pydantic models** for all API request and response schemas
- **async/await** for all FastAPI endpoints
- `fastapi.Depends` for dependency injection
- **No synchronous sqlite** in async paths — use aiosqlite exclusively
- **httpx async** for all outbound HTTP with explicit timeouts
- **No bare `print()` statements** — use structured logging
- Log tool calls with `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, `duration_ms`
- Ruff config: `line-length = 100`, `target-version = "py311"`, select `E, F, W, I, N, UP, B, C4`

## Building and Running

### Install Dependencies

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev
```

### Run Tests

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short
```

### Run Linter

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```

## Testing Requirements

- Use **pytest** with **pytest-asyncio** (`asyncio_mode = "auto"` is configured in pyproject.toml)
- Every MCP tool handler must have at least one **happy-path** and one **error-path** test
- Tests live in `tests/` mirroring the `src/` structure
- Junie **should run tests** before submitting to verify correctness
- Junie **should run ruff** to check for lint violations before submitting

## Workflow Context (Scafforge)

This project's tickets, folder structure, agent profiles, and workflow processes are generated by **Scafforge**, an external scaffolding tool wielded by a stronger AI. The in-repo AI agent (OpenCode with MiniMax-M2.7) follows a ticketed workflow with stage gates:

`planning → plan_review → implementation → review → QA → smoke_test → closeout`

### Key State Files

| File | Purpose |
|---|---|
| `tickets/manifest.json` | Machine-readable work queue |
| `.opencode/state/workflow-state.json` | Active ticket and stage state |
| `START-HERE.md` | Derived restart surface |
| `docs/spec/CANONICAL-BRIEF.md` | Canonical project definition |
| `docs/process/workflow.md` | Stage and proof contracts |
| `AGENTS.md` | Agent team, conventions, security rules |

### Diagnosis Folder

The `diagnosis/` directory at the project root contains timestamped report packs from overseer reviews. These are evidence surfaces — not implementation edits. New diagnosis reports should be created as markdown files in timestamped subdirectories.

## Important Rules for Junie

1. **Do not modify** files in `mcp_spec_pack/` — these are immutable reference material
2. **Do not modify** ticket state files (`tickets/manifest.json`, `.opencode/state/`) — these are managed by Scafforge tooling
3. **Do not use synchronous sqlite** calls in async code paths
4. **Always set explicit timeouts** on httpx calls
5. **Never log secrets** — redact tokens, passwords, and raw file contents
6. **Fail closed** — reject unknown nodes, repos, write targets, and service aliases
7. **Atomic writes** — use write-to-temp-then-rename for file delivery operations
8. **Path safety** — normalize all paths and reject traversal attempts (`..`, symlinks, absolute user paths)
