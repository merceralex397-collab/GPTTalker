# Ticket Board

| Wave | ID | Title | Lane | Stage | Status | Resolution | Verification | Parallel Safe | Overlap Risk | Depends On | Follow-ups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SETUP-001 | Project skeleton and dependency baseline | repo-foundation | closeout | done | done | trusted | no | high | - | - |
| 0 | SETUP-002 | Shared schemas, config loading, and structured logging | shared-runtime | closeout | done | done | suspect | no | medium | SETUP-001 | - |
| 0 | SETUP-003 | Async SQLite persistence and migration baseline | storage | closeout | done | done | suspect | no | medium | SETUP-001 | - |
| 0 | SETUP-004 | FastAPI hub app shell and MCP transport baseline | hub-core | closeout | done | done | suspect | no | high | SETUP-001, SETUP-002 | - |
| 0 | SETUP-005 | Test, lint, and local validation scaffold | qa | closeout | done | done | suspect | yes | low | SETUP-001 | - |
| 1 | CORE-001 | Node registry and node health model | registry | closeout | done | done | suspect | no | medium | SETUP-003, SETUP-004 | - |
| 1 | CORE-002 | Repo, write-target, and LLM service registries | registry | closeout | done | done | suspect | no | medium | SETUP-003, SETUP-004 | - |
| 1 | CORE-003 | Node agent service skeleton | node-agent | closeout | done | done | suspect | yes | low | SETUP-001, SETUP-002 | - |
| 1 | CORE-004 | Hub-to-node client, auth, and health polling | node-connectivity | closeout | done | done | suspect | no | high | CORE-001, CORE-003 | - |
| 1 | CORE-005 | Policy engine and normalized path validation | security | closeout | done | done | suspect | no | medium | SETUP-002, SETUP-004 | - |
| 1 | CORE-006 | MCP tool routing framework | hub-core | closeout | done | done | suspect | no | high | SETUP-004, CORE-002, CORE-005 | - |
| 2 | REPO-001 | list_nodes and list_repos tools | repo-inspection | closeout | done | done | suspect | yes | low | CORE-001, CORE-004, CORE-006 | - |
| 2 | REPO-002 | inspect_repo_tree and read_repo_file tools | repo-inspection | closeout | done | done | suspect | no | medium | CORE-004, CORE-005, CORE-006 | - |
| 2 | REPO-003 | search_repo and git_status tools | repo-inspection | closeout | done | done | suspect | no | medium | REPO-002 | - |
| 2 | WRITE-001 | write_markdown with atomic scoped writes | markdown | closeout | done | done | suspect | yes | low | CORE-002, CORE-004, CORE-005, CORE-006 | - |
| 2 | LLM-001 | chat_llm base routing and service registry integration | llm-routing | closeout | done | done | suspect | no | high | CORE-002, CORE-004, CORE-006 | - |
| 3 | LLM-002 | OpenCode adapter and session-aware coding-agent routing | llm-routing | closeout | done | done | suspect | no | medium | LLM-001 | - |
| 3 | LLM-003 | Helper-model and embedding-service adapters | llm-routing | closeout | done | done | suspect | yes | low | LLM-001 | - |
| 3 | CTX-001 | Qdrant integration and context storage schema | context | closeout | done | done | suspect | no | high | SETUP-003, LLM-003 | - |
| 3 | CTX-002 | index_repo pipeline and content-hash tracking | context | closeout | done | done | suspect | no | high | CTX-001, REPO-002 | - |
| 3 | CTX-003 | get_project_context and known-issue records | context | closeout | done | done | suspect | no | medium | CTX-001, CTX-002 | - |
| 3 | CTX-004 | Context bundles and recurring-issue workflows | context | closeout | done | done | suspect | yes | low | CTX-003 | - |
| 4 | XREPO-001 | Cross-repo search and global context query | cross-repo | closeout | done | done | suspect | no | medium | CTX-002, CTX-003 | - |
| 4 | XREPO-002 | Repo relationships and landscape metadata | cross-repo | closeout | done | done | suspect | yes | low | CORE-002, CTX-001 | - |
| 4 | XREPO-003 | Architecture map and project landscape outputs | cross-repo | closeout | done | done | suspect | no | medium | XREPO-001, XREPO-002 | - |
| 4 | SCHED-001 | Task classification and routing policy | scheduler | closeout | done | done | suspect | yes | low | LLM-001, CORE-002 | - |
| 4 | SCHED-002 | Distributed scheduler, node selection, and fallback | scheduler | closeout | done | done | suspect | no | high | SCHED-001, CORE-004, LLM-002 | - |
| 5 | OBS-001 | Task history, generated-doc log, and audit schema | observability | closeout | done | done | suspect | yes | low | SETUP-003, SETUP-002 | - |
| 5 | OBS-002 | Task detail, doc history, and issue timeline tools | observability | closeout | done | done | suspect | no | medium | OBS-001, CTX-003 | - |
| 5 | EDGE-001 | Cloudflare Tunnel integration and public-edge config | edge | closeout | done | done | suspect | yes | low | SETUP-004, CORE-005 | - |
| 5 | EDGE-002 | Node registration bootstrap and operator config docs | edge | closeout | done | done | suspect | yes | low | CORE-001, CORE-003, EDGE-001 | - |
| 6 | POLISH-001 | Contract tests for MCP tools and failure modes | qa | closeout | done | done | suspect | no | high | REPO-003, WRITE-001, LLM-002, CTX-003, OBS-002 | - |
| 6 | POLISH-002 | Security regression tests and redaction hardening | qa | closeout | done | done | suspect | no | medium | CORE-005, OBS-001, POLISH-001 | - |
| 6 | POLISH-003 | README, API docs, and handoff hardening | docs | closeout | done | done | suspect | yes | low | POLISH-001 | - |
| 7 | FIX-001 | Fix walrus operator syntax error in opencode.py | bugfix | closeout | done | done | reverified | no | high | - | - |
| 7 | FIX-002 | Fix Depends[] type subscript error in node agent | bugfix | closeout | done | done | reverified | yes | medium | - | - |
| 7 | FIX-003 | Fix hub MCP router async wiring and circular import | bugfix | closeout | done | done | reverified | no | high | FIX-001 | - |
| 7 | FIX-004 | Fix SQLite write persistence and uncommitted transactions | bugfix | closeout | done | done | reverified | yes | medium | - | - |
| 7 | FIX-005 | Fix structured logger TypeError and HubConfig attribute error | bugfix | closeout | done | done | reverified | yes | medium | - | - |
| 7 | FIX-006 | Register read_repo_file tool and close tool surface gaps | bugfix | closeout | done | done | reverified | yes | low | FIX-001, FIX-003 | - |
| 7 | FIX-007 | Fix ripgrep search parser and implement search modes | bugfix | closeout | done | done | reverified | yes | low | FIX-002 | - |
| 7 | FIX-008 | Add recent_commits to git_status output | bugfix | closeout | done | done | reverified | yes | low | FIX-002 | - |
| 7 | FIX-009 | Align write_markdown interface with spec contract | bugfix | closeout | done | done | reverified | yes | low | FIX-003 | - |
| 7 | FIX-010 | Implement missing observability tools and audit persistence | bugfix | closeout | done | done | reverified | yes | low | FIX-003, FIX-004 | - |
| 8 | FIX-011 | Complete aggregation service methods | completion | closeout | done | done | reverified | yes | low | FIX-004, FIX-010 | - |
| 8 | FIX-012 | Complete cross-repo landscape with real metrics | completion | closeout | done | done | reverified | yes | low | FIX-004 | - |
| 8 | FIX-013 | Implement Cloudflare Tunnel runtime management | completion | closeout | done | done | reverified | yes | low | FIX-003 | - |
| 8 | FIX-014 | Replace placeholder tests with real implementations | hardening | closeout | done | done | reverified | yes | low | FIX-001, FIX-002, FIX-003 | - |
| 8 | FIX-015 | Fix Task UUID handling and CLI entrypoint packaging | hardening | closeout | done | done | reverified | yes | low | - | - |
| 8 | FIX-016 | Security hardening - path validation and config safety | hardening | closeout | done | done | reverified | yes | low | FIX-002 | - |
| 8 | FIX-017 | Clean up duplicate endpoints, response models, and artifact registry | hardening | closeout | done | done | reverified | yes | low | FIX-003 | - |
| 9 | EXEC-001 | Fix node-agent FastAPI dependency injection import failure | bugfix | closeout | done | done | reverified | no | high | - | - |
| 9 | EXEC-002 | Restore pytest collection and full test execution after node-agent import fix | bugfix | closeout | done | done | reverified | no | high | EXEC-001 | EXEC-003, EXEC-004, EXEC-005, EXEC-006, EXEC-007, EXEC-008, EXEC-009, EXEC-010, EXEC-011 |
| 9 | EXEC-003 | Fix node-agent executor absolute-path validation within allowed roots | bugfix | closeout | done | done | reverified | yes | high | - | - |
| 9 | EXEC-004 | Fix hub repo-path normalization for inspection and file-read flows | bugfix | closeout | done | done | reverified | yes | high | - | - |
| 9 | EXEC-005 | Align write_markdown and MCP transport response contracts with tests | bugfix | closeout | done | done | reverified | yes | medium | - | - |
| 9 | EXEC-006 | Fix structured logging redaction behavior for nested payloads | bugfix | closeout | done | done | reverified | yes | medium | - | - |
| 10 | EXEC-007 | Restore discovery and inspection contract behavior in hub tools | bugfix | closeout | done | done | reverified | no | high | EXEC-004, EXEC-005 | EXEC-012 |
| 10 | EXEC-008 | Close remaining hub path and write-target security edge cases | security | closeout | done | done | reverified | no | high | EXEC-004 | EXEC-012 |
| 10 | EXEC-009 | Repair node-agent executor timestamp and recent-commit behavior | node-agent | closeout | done | done | reverified | yes | medium | EXEC-003 | - |
| 10 | EXEC-010 | Restore nested structured logging redaction semantics | shared-runtime | closeout | done | done | reverified | yes | medium | EXEC-006 | - |
| 10 | EXEC-011 | Reduce repo-wide ruff violations to zero | hardening | closeout | done | done | trusted | no | high | - | EXEC-013, EXEC-014 |
| 11 | EXEC-012 | Fix misclassified paths in test_path_traversal_dotdot_rejected and test_invalid_path_rejected | bugfix | closeout | done | superseded | reverified | yes | low | - | - |
| 11 | EXEC-013 | Fix datetime.UTC, collections.abc, and TimeoutError alias violations | bugfix | closeout | done | done | reverified | yes | low | - | - |
| 11 | EXEC-014 | Fix remaining mechanical Ruff violations after EXEC-013 | hardening | closeout | done | done | reverified | yes | low | EXEC-013 | - |
