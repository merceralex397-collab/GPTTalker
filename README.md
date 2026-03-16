# GPTTalker

A lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment. GPTTalker acts as a middleman service: ChatGPT sends requests via the MCP protocol, the hub enforces policy, routes work to the right machine over Tailscale, and returns structured results. It supports repo inspection, markdown delivery, LLM bridging, semantic project context via Qdrant, cross-repo intelligence, distributed LLM routing, and full observability — all without giving ChatGPT direct shell access to any machine.

## Key Features

- **Repo Inspection** — Browse file trees, read files, search code (text/path/symbol via ripgrep), and check git status on any registered repo across machines.
- **Markdown Delivery** — Atomic, policy-controlled markdown writes to approved locations with content hashing and audit logging.
- **LLM Bridge** — Route prompts to multiple LLM backends (coding agents, general LLMs, helper models, embedding services) with session support and timing metadata.
- **Project Context (Qdrant)** — Semantic vector memory per repo: architecture summaries, key file maps, recent docs, known issues, and natural-language queries over project history.
- **Cross-Repo Intelligence** — Global semantic search across all repos, relationship metadata, dependency graphs, and a unified project landscape view.
- **Distributed LLM Routing** — Multi-machine task classification and scheduling; route work to the best available backend based on task type, size, and machine health.
- **Observability** — Full audit trail: task history with trace IDs, generated document tracking, issue timelines, and per-tool call logging.
- **Node-Agent Architecture** — Hub coordinates; lightweight node agents run on each machine and handle local operations. All communication over Tailscale.

## Architecture Overview

```
┌──────────────┐         ┌─────────────────┐
│   ChatGPT    │◄───────►│ Cloudflare      │
│  (MCP client)│  HTTPS  │ Tunnel (edge)   │
└──────────────┘         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │   GPTTalker Hub │
                         │  (FastAPI, SQLite│
                         │   policy engine) │
                         └──┬─────┬─────┬──┘
                 Tailscale  │     │     │  Tailscale
                 ┌──────────▼┐ ┌──▼──┐ ┌▼──────────┐
                 │ Node Agent│ │Node │ │ Node Agent │
                 │ Machine A │ │Ag. B│ │ Machine C  │
                 │ (repos,   │ │     │ │ (repos,    │
                 │  LLMs)    │ │     │ │  embedding)│
                 └───────────┘ └─────┘ └────────────┘
```

- **ChatGPT → Hub**: MCP protocol over HTTPS via Cloudflare Tunnel (public edge).
- **Hub → Node Agents**: Authenticated HTTP over Tailscale (private mesh).
- **Hub**: Enforces policy (default-deny), validates targets, logs every call with trace IDs, manages node/repo registry in SQLite, and hosts Qdrant for project context.
- **Node Agents**: Lightweight services on each machine that execute local operations (file reads, git, ripgrep, LLM calls) and return structured results.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI |
| Structured storage | SQLite (via aiosqlite) |
| Vector store | Qdrant |
| Internal network | Tailscale |
| Public edge | Cloudflare Tunnel |
| Code search | ripgrep |
| Version control | git CLI |
| HTTP client | httpx (async) |
| Linting | ruff |
| Testing | pytest |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/GPTTalker.git
cd GPTTalker

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy and edit configuration
cp config/example.toml config/local.toml
# Edit config/local.toml with your Tailscale node addresses,
# Qdrant connection, LLM backend URLs, and Cloudflare Tunnel token.

# Run the hub
python -m src.hub.main

# On each machine, run the node agent
python -m src.node_agent.main --config config/node.toml
```

## Project Structure

```
GPTTalker/
├── src/
│   ├── hub/                  # Main hub server
│   │   ├── main.py           # FastAPI application entrypoint
│   │   ├── tool_handlers/    # MCP tool handler implementations
│   │   ├── policy.py         # Policy engine (default-deny, target validation)
│   │   └── context.py        # Context manager (Qdrant integration)
│   ├── node_agent/           # Node agent service
│   │   ├── main.py           # Node agent entrypoint
│   │   ├── executors/        # Local operation executors (file, git, search, LLM)
│   │   └── health.py         # Health check and registration
│   └── shared/               # Shared models and utilities
│       ├── models.py         # Pydantic request/response schemas
│       ├── logging.py        # Structured logging with trace IDs
│       └── security.py       # Path normalization, redaction, validation
├── docs/                     # Specs and process docs
│   ├── spec/
│   │   └── CANONICAL-BRIEF.md
│   └── process/
│       ├── workflow.md
│       ├── agent-catalog.md
│       └── model-matrix.md
├── tickets/                  # Work queue
│   ├── BOARD.md
│   └── manifest.json
├── .opencode/                # Agent team and workflow
│   ├── agents/               # Agent prompt files
│   ├── state/                # Workflow state and artifacts
│   └── meta/                 # Bootstrap provenance
├── mcp_spec_pack/            # MCP specification documents
├── config/                   # Configuration files
├── AGENTS.md                 # Coding conventions and agent rules
├── START-HERE.md             # Handoff / resume surface
└── README.md
```

## MCP Tools Reference

### V1 — Core Tools

| Tool | Purpose | Key Parameters |
|---|---|---|
| `list_nodes` | List managed machines | — |
| `list_repos` | List registered repos on a node | `node` |
| `inspect_repo_tree` | View file tree | `node`, `repo`, `path` |
| `read_repo_file` | Read file contents | `node`, `repo`, `file_path` |
| `search_repo` | Search code (text/path/symbol) | `node`, `repo`, `query`, `mode` |
| `git_status` | View git status | `node`, `repo` |
| `write_markdown` | Atomic markdown write to approved locations | `node`, `write_target`, `relative_path`, `content`, `mode` |
| `chat_llm` | Route prompt to an LLM backend | `node`, `service`, `prompt`, `context`, `session_id` |
| `index_repo` | Build/refresh project context | `node`, `repo` |
| `get_project_context` | Query semantic project memory | `node`, `repo`, `query` |
| `list_known_issues` | View known issues for a repo | `node`, `repo` |
| `record_issue` | Manually record an issue | `node`, `repo`, `title`, `summary`, `severity` |
| `list_task_history` | View task audit trail | `filters` |

### V2 — Advanced Tools

| Tool | Purpose | Key Parameters |
|---|---|---|
| `build_context_bundle` | Tailored context for a task type | `node`, `repo`, `task_type`, `query` |
| `list_recurring_issues` | Track recurring problem patterns | `node`, `repo` |
| `get_architecture_map` | Module/service dependency graph | `node`, `repo` |
| `search_global_context` | Cross-repo semantic search | `query` |
| `search_across_repos` | Global project text search | `query` |
| `list_related_repos` | Find related projects | `repo` |
| `get_project_landscape` | Overall project map | — |
| `route_task` | Distributed LLM task routing | `task_type`, `preferred_repo`, `size_hint` |
| `get_task_details` | Full task record with trace | `task_id` |
| `list_generated_docs` | Generated file history | `repo` |
| `get_issue_timeline` | Issue history over time | `repo` |

## Documentation

- **[AGENTS.md](AGENTS.md)** — Coding conventions, agent rules, and security policies
- **[docs/spec/CANONICAL-BRIEF.md](docs/spec/CANONICAL-BRIEF.md)** — Canonical project brief (source of truth)
- **[tickets/BOARD.md](tickets/BOARD.md)** — Current work queue
- **[START-HERE.md](START-HERE.md)** — Handoff and resume surface

## License

See [LICENSE](LICENSE) for details.
