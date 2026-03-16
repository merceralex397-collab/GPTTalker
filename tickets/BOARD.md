# Ticket Board

| Wave | ID | Title | Lane | Stage | Status | Parallel Safe | Overlap Risk | Depends On |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SETUP-001 | Project skeleton and dependency baseline | repo-foundation | planning | ready | no | high | - |
| 0 | SETUP-002 | Shared schemas, config loading, and structured logging | shared-runtime | planning | todo | no | medium | SETUP-001 |
| 0 | SETUP-003 | Async SQLite persistence and migration baseline | storage | planning | todo | no | medium | SETUP-001 |
| 0 | SETUP-004 | FastAPI hub app shell and MCP transport baseline | hub-core | planning | todo | no | high | SETUP-001, SETUP-002 |
| 0 | SETUP-005 | Test, lint, and local validation scaffold | qa | planning | todo | yes | low | SETUP-001 |
| 1 | CORE-001 | Node registry and node health model | registry | planning | todo | no | medium | SETUP-003, SETUP-004 |
| 1 | CORE-002 | Repo, write-target, and LLM service registries | registry | planning | todo | no | medium | SETUP-003, SETUP-004 |
| 1 | CORE-003 | Node agent service skeleton | node-agent | planning | todo | yes | low | SETUP-001, SETUP-002 |
| 1 | CORE-004 | Hub-to-node client, auth, and health polling | node-connectivity | planning | todo | no | high | CORE-001, CORE-003 |
| 1 | CORE-005 | Policy engine and normalized path validation | security | planning | todo | no | medium | SETUP-002, SETUP-004 |
| 1 | CORE-006 | MCP tool routing framework | hub-core | planning | todo | no | high | SETUP-004, CORE-002, CORE-005 |
| 2 | REPO-001 | list_nodes and list_repos tools | repo-inspection | planning | todo | yes | low | CORE-001, CORE-004, CORE-006 |
| 2 | REPO-002 | inspect_repo_tree and read_repo_file tools | repo-inspection | planning | todo | no | medium | CORE-004, CORE-005, CORE-006 |
| 2 | REPO-003 | search_repo and git_status tools | repo-inspection | planning | todo | no | medium | REPO-002 |
| 2 | WRITE-001 | write_markdown with atomic scoped writes | markdown | planning | todo | yes | low | CORE-002, CORE-004, CORE-005, CORE-006 |
| 2 | LLM-001 | chat_llm base routing and service registry integration | llm-routing | planning | todo | no | high | CORE-002, CORE-004, CORE-006 |
| 3 | LLM-002 | OpenCode adapter and session-aware coding-agent routing | llm-routing | planning | todo | no | medium | LLM-001 |
| 3 | LLM-003 | Helper-model and embedding-service adapters | llm-routing | planning | todo | yes | low | LLM-001 |
| 3 | CTX-001 | Qdrant integration and context storage schema | context | planning | todo | no | high | SETUP-003, LLM-003 |
| 3 | CTX-002 | index_repo pipeline and content-hash tracking | context | planning | todo | no | high | CTX-001, REPO-002 |
| 3 | CTX-003 | get_project_context and known-issue records | context | planning | todo | no | medium | CTX-001, CTX-002 |
| 3 | CTX-004 | Context bundles and recurring-issue workflows | context | planning | todo | yes | low | CTX-003 |
| 4 | XREPO-001 | Cross-repo search and global context query | cross-repo | planning | todo | no | medium | CTX-002, CTX-003 |
| 4 | XREPO-002 | Repo relationships and landscape metadata | cross-repo | planning | todo | yes | low | CORE-002, CTX-001 |
| 4 | XREPO-003 | Architecture map and project landscape outputs | cross-repo | planning | todo | no | medium | XREPO-001, XREPO-002 |
| 4 | SCHED-001 | Task classification and routing policy | scheduler | planning | todo | yes | low | LLM-001, CORE-002 |
| 4 | SCHED-002 | Distributed scheduler, node selection, and fallback | scheduler | planning | todo | no | high | SCHED-001, CORE-004, LLM-002 |
| 5 | OBS-001 | Task history, generated-doc log, and audit schema | observability | planning | todo | yes | low | SETUP-003, SETUP-002 |
| 5 | OBS-002 | Task detail, doc history, and issue timeline tools | observability | planning | todo | no | medium | OBS-001, CTX-003 |
| 5 | EDGE-001 | Cloudflare Tunnel integration and public-edge config | edge | planning | todo | yes | low | SETUP-004, CORE-005 |
| 5 | EDGE-002 | Node registration bootstrap and operator config docs | edge | planning | todo | yes | low | CORE-001, CORE-003, EDGE-001 |
| 6 | POLISH-001 | Contract tests for MCP tools and failure modes | qa | planning | todo | no | high | REPO-003, WRITE-001, LLM-002, CTX-003, OBS-002 |
| 6 | POLISH-002 | Security regression tests and redaction hardening | qa | planning | todo | no | medium | CORE-005, OBS-001, POLISH-001 |
| 6 | POLISH-003 | README, API docs, and handoff hardening | docs | planning | todo | yes | low | POLISH-001 |
