# GPTTalker

GPTTalker is a lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment.

## Current status

- The managed workflow layer was repaired on March 25, 2026 to restore closed-ticket reverification and contradiction-stop behavior.
- The runtime environment is bootstrapped with `uv`, the dev dependencies are installed, and repo-managed validation commands execute.
- Historical done tickets still require backlog reverification before `pending_process_verification` can be cleared.
- Wave 10 remediation tickets `EXEC-007` through `EXEC-011` now track the remaining 13 failing tests plus repo-wide lint debt.
- The system includes:
  - FastAPI MCP hub with policy-controlled tools
  - Node agent service for distributed execution
  - SQLite registry and history storage
  - Qdrant vector store for project context
  - ngrok integration for public HTTPS edge
  - Security-focused fail-closed design

## Implemented Features

### Core Infrastructure
- Python + FastAPI MCP hub server
- Node agent service with health endpoints
- SQLite persistence with async aiosqlite
- Qdrant integration for semantic search

### MCP Tools
- Discovery: list_nodes, list_repos
- Inspection: inspect_repo_tree, read_repo_file
- Search: search_repo, git_status
- Write: write_markdown (atomic, extension-validated)
- LLM: chat_llm, chat_opencode, chat_embeddings
- Context: index_repo, get_project_context, record_issue
- Cross-repo: search_across_repos, get_project_landscape
- Architecture: get_architecture_map, get_repo_architecture
- Observability: get_task_details, list_generated_docs, get_issue_timeline

### Security
- Policy engine with fail-closed behavior
- Path normalization and traversal prevention
- Extension allowlists for write operations
- Structured logging with secret redaction

## Repository layout

- `src/hub/` — FastAPI MCP hub implementation
- `src/node_agent/` — Node agent service
- `src/shared/` — Shared schemas, repositories, config
- `docs/` — Operation and API documentation
- `tests/` — Contract and security tests
- `tickets/` — Completed ticket backlog

## Getting Started

1. Read `START-HERE.md` for operational guidance
2. Review `docs/process/workflow.md` and `tickets/BOARD.md`
3. Run `UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev`
4. Configure environment variables for hub, nodes, and ngrok if you want the public edge enabled

## Resume contract

- Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first.
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces.
- Treat the active open ticket as the primary lane even when historical reverification is pending.

## Testing

Run tests with:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
```
