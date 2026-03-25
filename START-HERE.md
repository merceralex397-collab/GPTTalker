# GPTTalker — START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## Project

GPTTalker

## Workflow State

- process_version: 5
- parallel_mode: parallel-lanes
- pending_process_verification: true
- bootstrap_status: ready
- bootstrap_proof: .opencode/state/artifacts/history/exec-001/bootstrap/2026-03-25T12-05-00-000Z-environment-bootstrap.md

## Current Ticket

- ID: EXEC-001
- Title: Fix node-agent FastAPI dependency injection import failure
- Wave: 9
- Lane: bugfix
- Stage: smoke_test
- Status: smoke_test
- Resolution: open
- Verification: suspect

## Reopened Tickets

- None

## Done But Not Fully Trusted

- SETUP-001: Project skeleton and dependency baseline
- SETUP-002: Shared schemas, config loading, and structured logging
- SETUP-003: Async SQLite persistence and migration baseline
- SETUP-004: FastAPI hub app shell and MCP transport baseline
- SETUP-005: Test, lint, and local validation scaffold
- CORE-001: Node registry and node health model
- CORE-002: Repo, write-target, and LLM service registries
- CORE-003: Node agent service skeleton
- CORE-004: Hub-to-node client, auth, and health polling
- CORE-005: Policy engine and normalized path validation
- CORE-006: MCP tool routing framework
- REPO-001: list_nodes and list_repos tools
- REPO-002: inspect_repo_tree and read_repo_file tools
- REPO-003: search_repo and git_status tools
- WRITE-001: write_markdown with atomic scoped writes
- LLM-001: chat_llm base routing and service registry integration
- LLM-002: OpenCode adapter and session-aware coding-agent routing
- LLM-003: Helper-model and embedding-service adapters
- CTX-001: Qdrant integration and context storage schema
- CTX-002: index_repo pipeline and content-hash tracking
- CTX-003: get_project_context and known-issue records
- CTX-004: Context bundles and recurring-issue workflows
- XREPO-001: Cross-repo search and global context query
- XREPO-002: Repo relationships and landscape metadata
- XREPO-003: Architecture map and project landscape outputs
- SCHED-001: Task classification and routing policy
- SCHED-002: Distributed scheduler, node selection, and fallback
- OBS-001: Task history, generated-doc log, and audit schema
- OBS-002: Task detail, doc history, and issue timeline tools
- EDGE-001: Cloudflare Tunnel integration and public-edge config
- EDGE-002: Node registration bootstrap and operator config docs
- POLISH-001: Contract tests for MCP tools and failure modes
- POLISH-002: Security regression tests and redaction hardening
- POLISH-003: README, API docs, and handoff hardening
- FIX-001: Fix walrus operator syntax error in opencode.py
- FIX-002: Fix Depends[] type subscript error in node agent
- FIX-003: Fix hub MCP router async wiring and circular import
- FIX-004: Fix SQLite write persistence and uncommitted transactions
- FIX-005: Fix structured logger TypeError and HubConfig attribute error
- FIX-006: Register read_repo_file tool and close tool surface gaps
- FIX-007: Fix ripgrep search parser and implement search modes
- FIX-008: Add recent_commits to git_status output
- FIX-009: Align write_markdown interface with spec contract
- FIX-010: Implement missing observability tools and audit persistence
- FIX-011: Complete aggregation service methods
- FIX-012: Complete cross-repo landscape with real metrics
- FIX-013: Implement Cloudflare Tunnel runtime management
- FIX-014: Replace placeholder tests with real implementations
- FIX-015: Fix Task UUID handling and CLI entrypoint packaging
- FIX-016: Security hardening - path validation and config safety
- FIX-017: Clean up duplicate endpoints, response models, and artifact registry

## Pending Reverification

- None

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/BOARD.md
6. tickets/manifest.json

## Next Action

EXEC-001 SOURCE FIX VERIFIED — node-agent imports cleanly (dependencies.py uses request:Request pattern). Implementation, code review, QA all PASSED. Closeout BLOCKED: smoke_test tool uses system python3 (no pytest) vs acceptance criteria requiring .venv/bin/pytest. Tool/env mismatch, not a code defect. EXEC-002 (pytest collection) depends on EXEC-001 "done" status but closeout gate cannot clear this tool limitation. Fix requires smoke_test tool to use venv python or accept custom commands. 17 suspect FIX tickets still need backlog verification.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
