# GPTTalker — Canonical Brief

## 1. Project Summary

GPTTalker is a lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment. It acts as a middleman service: ChatGPT sends requests via the MCP protocol, the hub enforces policy, routes work to the right machine over Tailscale, and returns structured results. The system supports repo inspection, LLM bridging, markdown delivery, persistent project context with semantic search, cross-repo intelligence, distributed model routing, and full observability — all scoped to approved targets with no unrestricted shell access.

## 2. Goals

- Provide safe, policy-controlled ChatGPT access to development repos across multiple machines
- Support read-only repo inspection: file trees, file reading, text/symbol search, git status, recent commits
- Support controlled markdown delivery to approved write roots
- Support LLM bridging: route prompts to approved local models, coding agents (OpenCode), helper models, and embedding services
- Support persistent project context: per-repo summaries, file summaries, issue records, semantic vector search via Qdrant
- Support cross-repo intelligence: global search, relationship metadata, dependency/architecture graphs
- Support distributed LLM execution: multi-machine model routing, task classification, scheduler policies, health checks
- Support full observability: task history, generated document history, issue timelines, audit logs
- Support node-agent architecture: lightweight agent on each managed machine, hub routes over Tailscale
- Expose a public HTTPS edge via Cloudflare Tunnel for ChatGPT MCP connectivity
- Keep the hub lightweight enough to run on an older laptop
- Fail closed on unknown targets, missing aliases, and invalid paths
- Persist all config, registry, and history state across restarts

## 3. Non-Goals

- Unrestricted shell execution on any machine
- Arbitrary filesystem writes outside approved write roots
- Autonomous code editing without review
- Direct git commit / push actions
- Wide-open remote control of every machine
- Multi-user or multi-tenant access (single-operator deployment)

## 4. Constraints

- **Runtime**: Python 3.11+, FastAPI
- **Database**: SQLite for structured records (registry, history, task records)
- **Vector store**: Qdrant for semantic project context retrieval
- **Internal connectivity**: Tailscale tailnet (private, all hub-to-node traffic)
- **Public edge**: Cloudflare Tunnel (HTTPS, no inbound ports)
- **Node architecture**: Lightweight Python agent on each managed machine
- **LLM runtimes**: OpenCode for coding-agent workflows; llama.cpp-class serving for local CPU inference; dedicated embedding service
- **Deployment**: Hub on older laptop; main LLM on stronger machine; repos spread across multiple machines
- **Security**: Default deny for unknown nodes/repos; HTTPS public edge; Tailscale internal; no secrets in logs or generated docs; Tailscale + app-level API keys for service auth
- **Agent model**: All OpenCode agents use `minimax-coding-plan/MiniMax-M2.5`
- **Workflow**: local-git-capable, ticketed, deterministic
- **Agent design**: autonomous with internal gates, no `ask`
- **OpenCode layer**: commands for humans, tools/plugins for autonomy

## 5. Required Outputs

- Python + FastAPI MCP hub server with tool exposure layer
- Node agent Python service (runs on each managed machine)
- Repo inspection tools: `list_repos`, `inspect_repo_tree`, `read_repo_file`, `search_repo`, `git_status`
- Markdown delivery tools: `write_markdown` with atomic writes, extension allowlist, write-target scoping
- LLM bridge tools: `chat_llm` with service alias routing, OpenCode adapter, session support
- Project context system: `index_repo`, `get_project_context`, `list_known_issues`, `record_issue` with Qdrant vector index + SQLite structured store
- Cross-repo intelligence: `search_across_repos`, `list_related_repos`, `get_project_landscape`, `get_architecture_map`
- Distributed LLM routing: `route_task` with task classification, model registry, health checks, fallback policies
- Observability: `list_task_history`, `get_task_details`, `list_generated_docs`, `get_issue_timeline`
- Advanced context: `build_context_bundle`, `list_recurring_issues`, `search_global_context`
- Node management: `list_nodes` with health checks
- Registry management: node registry, repo registry, write-target registry, LLM service registry
- Cloudflare Tunnel configuration for public HTTPS edge
- Full test suite covering tool contracts, policy enforcement, failure modes

## 6. Tooling and Model Constraints

- **Provider**: `minimax-coding-plan`
- **Planner/reviewer model**: `minimax-coding-plan/MiniMax-M2.5`
- **Implementer model**: `minimax-coding-plan/MiniMax-M2.5`
- **Utility/helper model**: `minimax-coding-plan/MiniMax-M2.5`
- **Runtime**: Python 3.11+ with FastAPI, uvicorn
- **Hub host**: Older laptop (resource-constrained)
- **Main LLM host**: Stronger machine (32GB CPU-only)
- **Repo inspection tools**: ripgrep for search, git CLI for status/commits
- **Vector DB**: Qdrant (self-hosted or embedded)
- **Structured DB**: SQLite
- **Package management**: uv or pip
- **Testing**: pytest
- **Linting**: ruff

## 7. Canonical Truth Map

| Kind of state | Owner file |
|---|---|
| Project definition | `docs/spec/CANONICAL-BRIEF.md` |
| Work queue | `tickets/manifest.json` |
| Work queue human view | `tickets/BOARD.md` (derived) |
| Active ticket / stage | `.opencode/state/workflow-state.json` |
| Artifact registry | `.opencode/state/artifacts/registry.json` |
| Bootstrap provenance | `.opencode/meta/bootstrap-provenance.json` |
| Agent prompts | `.opencode/agents/*.md` |
| Agent team overview | `AGENTS.md` |
| Repo conventions | `AGENTS.md` |
| Process workflow | `docs/process/workflow.md` |
| Handoff / resume | `START-HERE.md` |
| Hub configuration | `src/hub/config/` (runtime config files) |
| Node registry | SQLite `nodes` table (runtime) |
| Repo registry | SQLite `repos` table (runtime) |
| Task history | SQLite `tasks` table (runtime) |
| Project context vectors | Qdrant collections (runtime) |

## 8. Blocking Decisions

All blocking decisions have been resolved:

| Decision | Choice | Rationale |
|---|---|---|
| Project name | GPTTalker | User-specified |
| Stack | Python + FastAPI | Lightweight, hub-friendly |
| Architecture | Node-agent | Recommended for multi-machine growth |
| Public edge | Cloudflare Tunnel | Production-grade, no inbound ports |
| Vector DB | Qdrant | Robust filtering, durable search |
| Structured DB | SQLite | Lightweight for hub laptop |
| Scope | Combined V1+V2 | All features in single scope |
| Agent model | minimax-coding-plan/MiniMax-M2.5 | User-specified for all agents |
| Internal connectivity | Tailscale | Hard-set from specs |
| Auth model | Tailscale + app-level API keys | Balance of simplicity and security |
| Repo discovery | Assisted (scan + manual approval) | Safe but convenient |
| Indexing triggers | Manual + write-triggered + scheduled fallback | Strongest hybrid approach |
| Context sources | All tiers (docs, code summaries, commits, issues, architecture, history) | Maximum project intelligence |
| LLM runtimes | OpenCode + llama.cpp-class + dedicated embedding | Specialized distributed model |

## 9. Non-Blocking Open Questions

- Exact embedding model choice for Qdrant indexing (can be decided during implementation)
- Specific llama.cpp-compatible model to run on the 32GB machine
- Qdrant deployment mode: embedded vs. standalone service
- Whether to include a small helper model on the hub machine itself
- Specific Cloudflare Tunnel configuration details (domain, access policies)
- Git hook integration details for indexing triggers
- Scheduled indexing interval
- Knowledge graph storage backend (can be deferred to later tickets)
- Context bundle template format
- Exact file extension allowlist for markdown delivery beyond `.md` and `.txt`

## 10. Backlog Readiness

The backlog is ready for full ticketing. All blocking architectural, stack, and provider decisions are resolved. No feature area is blocked on unresolved major choices.

Ticketing can proceed for all areas:
- Hub core infrastructure and tool framework
- Node agent service
- Repo inspection tools
- Markdown delivery tools
- LLM bridge and routing
- Project context and Qdrant integration
- Cross-repo intelligence
- Distributed LLM scheduling
- Observability and history
- Cloudflare Tunnel public edge
- Security and registry management
- Testing and validation

## 11. Acceptance Signals

- Hub starts and exposes MCP-compliant tools over HTTPS via Cloudflare Tunnel
- ChatGPT can call `list_nodes`, `list_repos`, `inspect_repo_tree`, `read_repo_file`, `search_repo`, `git_status` against approved repos on remote machines
- ChatGPT can call `write_markdown` to approved write roots with atomic writes and extension enforcement
- ChatGPT can call `chat_llm` to route prompts to approved LLM backends
- ChatGPT can call `index_repo` and `get_project_context` with semantic Qdrant retrieval
- ChatGPT can call `search_across_repos` for cross-repo intelligence
- ChatGPT can call `route_task` and the scheduler selects appropriate backends
- All tool calls are logged with timestamp, caller, target, outcome, trace ID
- Unauthorized paths, repos, nodes, and services are rejected (fail closed)
- Hub persists state across restarts
- Node agents respond to health checks and execute scoped operations
- Observability tools return task history, document history, issue timelines

## 12. Assumptions

- The operator has a working Tailscale tailnet connecting all machines
- The operator has a Cloudflare account for tunnel configuration
- Target machines run Linux (for node agent deployment)
- The hub laptop runs Windows or Linux with Python 3.11+
- Qdrant can run on the hub machine or a dedicated machine on the tailnet
- The 32GB machine is available for main LLM workloads
- ChatGPT MCP integration follows the OpenAI MCP protocol as documented
- The operator manages a small number of machines (single-digit) in a home-lab environment
- Network latency over Tailscale is acceptable for interactive ChatGPT tool use
