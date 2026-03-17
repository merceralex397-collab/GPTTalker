# GPTTalker

GPTTalker is a lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment.

## Current status

- All 32 tickets have been completed (waves 0-6)
- The system is fully implemented with:
  - FastAPI MCP hub with policy-controlled tools
  - Node agent service for distributed execution
  - SQLite registry and history storage
  - Qdrant vector store for project context
  - Cloudflare Tunnel integration for public HTTPS edge
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
2. Review `docs/ops/` for setup guides
3. Configure environment variables for hub and nodes

## Testing

Run tests with:
```bash
pytest tests/
ruff check src/
```
