# Ticket Board

| Wave | ID | Title | Lane | Stage | Status | Parallel Safe | Overlap Risk | Depends On |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SETUP-001 | Project skeleton and dependency baseline | repo-foundation | closeout | done | no | high | - |
| 0 | SETUP-002 | Shared schemas, config loading, and structured logging | shared-runtime | closeout | done | no | medium | SETUP-001 |
| 0 | SETUP-003 | Async SQLite persistence and migration baseline | storage | closeout | done | no | medium | SETUP-001 |
| 0 | SETUP-004 | FastAPI hub app shell and MCP transport baseline | hub-core | closeout | done | no | high | SETUP-001, SETUP-002 |
| 0 | SETUP-005 | Test, lint, and local validation scaffold | qa | closeout | done | yes | low | SETUP-001 |
| 1 | CORE-001 | Node registry and node health model | registry | closeout | done | no | medium | SETUP-003, SETUP-004 |
| 1 | CORE-002 | Repo, write-target, and LLM service registries | registry | closeout | done | no | medium | SETUP-003, SETUP-004 |
| 1 | CORE-003 | Node agent service skeleton | node-agent | closeout | done | yes | low | SETUP-001, SETUP-002 |
| 1 | CORE-004 | Hub-to-node client, auth, and health polling | node-connectivity | closeout | done | no | high | CORE-001, CORE-003 |
| 1 | CORE-005 | Policy engine and normalized path validation | security | closeout | done | no | medium | SETUP-002, SETUP-004 |
| 1 | CORE-006 | MCP tool routing framework | hub-core | closeout | done | no | high | SETUP-004, CORE-002, CORE-005 |
| 2 | REPO-001 | list_nodes and list_repos tools | repo-inspection | closeout | done | yes | low | CORE-001, CORE-004, CORE-006 |
| 2 | REPO-002 | inspect_repo_tree and read_repo_file tools | repo-inspection | closeout | done | no | medium | CORE-004, CORE-005, CORE-006 |
| 2 | REPO-003 | search_repo and git_status tools | repo-inspection | closeout | done | no | medium | REPO-002 |
| 2 | WRITE-001 | write_markdown with atomic scoped writes | markdown | closeout | done | yes | low | CORE-002, CORE-004, CORE-005, CORE-006 |
| 2 | LLM-001 | chat_llm base routing and service registry integration | llm-routing | closeout | done | no | high | CORE-002, CORE-004, CORE-006 |
| 3 | LLM-002 | OpenCode adapter and session-aware coding-agent routing | llm-routing | closeout | done | no | medium | LLM-001 |
| 3 | LLM-003 | Helper-model and embedding-service adapters | llm-routing | closeout | done | yes | low | LLM-001 |
| 3 | CTX-001 | Qdrant integration and context storage schema | context | closeout | done | no | high | SETUP-003, LLM-003 |
| 3 | CTX-002 | index_repo pipeline and content-hash tracking | context | closeout | done | no | high | CTX-001, REPO-002 |
| 3 | CTX-003 | get_project_context and known-issue records | context | closeout | done | no | medium | CTX-001, CTX-002 |
| 3 | CTX-004 | Context bundles and recurring-issue workflows | context | closeout | done | yes | low | CTX-003 |
| 4 | XREPO-001 | Cross-repo search and global context query | cross-repo | closeout | done | no | medium | CTX-002, CTX-003 |
| 4 | XREPO-002 | Repo relationships and landscape metadata | cross-repo | closeout | done | yes | low | CORE-002, CTX-001 |
| 4 | XREPO-003 | Architecture map and project landscape outputs | cross-repo | closeout | done | no | medium | XREPO-001, XREPO-002 |
| 4 | SCHED-001 | Task classification and routing policy | scheduler | closeout | done | yes | low | LLM-001, CORE-002 |
| 4 | SCHED-002 | Distributed scheduler, node selection, and fallback | scheduler | closeout | done | no | high | SCHED-001, CORE-004, LLM-002 |
| 5 | OBS-001 | Task history, generated-doc log, and audit schema | observability | closeout | done | yes | low | SETUP-003, SETUP-002 |
| 5 | OBS-002 | Task detail, doc history, and issue timeline tools | observability | closeout | done | no | medium | OBS-001, CTX-003 |
| 5 | EDGE-001 | Cloudflare Tunnel integration and public-edge config | edge | closeout | done | yes | low | SETUP-004, CORE-005 |
| 5 | EDGE-002 | Node registration bootstrap and operator config docs | edge | closeout | done | yes | low | CORE-001, CORE-003, EDGE-001 |
| 6 | POLISH-001 | Contract tests for MCP tools and failure modes | qa | closeout | done | no | high | REPO-003, WRITE-001, LLM-002, CTX-003, OBS-002 |
| 6 | POLISH-002 | Security regression tests and redaction hardening | qa | closeout | done | no | medium | CORE-005, OBS-001, POLISH-001 |
| 6 | POLISH-003 | README, API docs, and handoff hardening | docs | closeout | done | yes | low | POLISH-001 |
| 7 | FIX-001 | Fix walrus operator syntax error in opencode.py | bugfix | closeout | done | no | high | - |
| 7 | FIX-002 | Fix Depends[] type subscript error in node agent | bugfix | closeout | done | yes | medium | - |
| 7 | FIX-003 | Fix hub MCP router async wiring and circular import | bugfix | closeout | done | no | high | FIX-001 |
| 7 | FIX-004 | Fix SQLite write persistence and uncommitted transactions | bugfix | closeout | done | yes | medium | - |
| 7 | FIX-005 | Fix structured logger TypeError and HubConfig attribute error | bugfix | closeout | done | yes | medium | - |
| 7 | FIX-006 | Register read_repo_file tool and close tool surface gaps | bugfix | closeout | done | yes | low | FIX-001, FIX-003 |
| 7 | FIX-007 | Fix ripgrep search parser and implement search modes | bugfix | closeout | done | yes | low | FIX-002 |
| 7 | FIX-008 | Add recent_commits to git_status output | bugfix | closeout | done | yes | low | FIX-002 |
| 7 | FIX-009 | Align write_markdown interface with spec contract | bugfix | closeout | done | yes | low | FIX-003 |
| 7 | FIX-010 | Implement missing observability tools and audit persistence | bugfix | closeout | done | yes | low | FIX-003, FIX-004 |
| 8 | FIX-011 | Complete aggregation service methods | completion | closeout | done | yes | low | FIX-004, FIX-010 |
| 8 | FIX-012 | Complete cross-repo landscape with real metrics | completion | closeout | done | yes | low | FIX-004 |
| 8 | FIX-013 | Implement Cloudflare Tunnel runtime management | completion | closeout | done | yes | low | FIX-003 |
| 8 | FIX-014 | Replace placeholder tests with real implementations | hardening | closeout | done | yes | low | FIX-001, FIX-002, FIX-003 |
| 8 | FIX-015 | Fix Task UUID handling and CLI entrypoint packaging | hardening | closeout | done | yes | low | - |
| 8 | FIX-016 | Security hardening - path validation and config safety | hardening | closeout | done | yes | low | FIX-002 |
| 8 | FIX-017 | Clean up duplicate endpoints, response models, and artifact registry | hardening | closeout | done | yes | low | FIX-003 |
