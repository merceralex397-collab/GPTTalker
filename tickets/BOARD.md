# GPTTalker — Ticket Board

> **Active ticket:** `SETUP-001`
> **Total tickets:** 39 | **Todo:** 35 | **Blocked:** 4 | **Done:** 0

---

## Wave 0: Foundation

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [SETUP-001](SETUP-001.md) | Project skeleton and dependencies | 🟡 todo | — |
| [SETUP-002](SETUP-002.md) | Hub FastAPI application skeleton | 🟡 todo | SETUP-001 |
| [SETUP-003](SETUP-003.md) | SQLite database layer | 🟡 todo | SETUP-001 |
| [SETUP-004](SETUP-004.md) | Logging and error handling | 🟡 todo | SETUP-002 |
| [SETUP-005](SETUP-005.md) | Test infrastructure | 🟡 todo | SETUP-001 |

## Wave 1: Core Infrastructure

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [CORE-001](CORE-001.md) | Node registry and management | 🟡 todo | SETUP-003, SETUP-002 |
| [CORE-002](CORE-002.md) | Node agent service skeleton | 🟡 todo | SETUP-001 |
| [CORE-003](CORE-003.md) | Hub-to-node connectivity layer | 🟡 todo | CORE-001, CORE-002 |
| [CORE-004](CORE-004.md) | Repo registry and validation | 🟡 todo | CORE-001, SETUP-003 |
| [CORE-005](CORE-005.md) | Write-target registry | 🟡 todo | CORE-001, SETUP-003 |
| [CORE-006](CORE-006.md) | LLM service registry | 🟡 todo | CORE-001, SETUP-003 |
| [CORE-007](CORE-007.md) | MCP protocol layer | 🟡 todo | SETUP-002, SETUP-004 |

## Wave 2: Repo Inspection

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [REPO-001](REPO-001.md) | inspect_repo_tree tool | 🟡 todo | CORE-003, CORE-004 |
| [REPO-002](REPO-002.md) | read_repo_file tool | 🟡 todo | CORE-003, CORE-004 |
| [REPO-003](REPO-003.md) | search_repo tool | 🟡 todo | CORE-003, CORE-004 |
| [REPO-004](REPO-004.md) | git_status tool | 🟡 todo | CORE-003, CORE-004 |

## Wave 3: Markdown Delivery

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [WRITE-001](WRITE-001.md) | write_markdown tool | 🟡 todo | CORE-003, CORE-005 |

## Wave 4: LLM Bridge

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [LLM-001](LLM-001.md) | chat_llm tool | 🟡 todo | CORE-003, CORE-006 |
| [LLM-002](LLM-002.md) | OpenCode adapter | 🟡 todo | LLM-001 |
| [LLM-003](LLM-003.md) | General and helper model adapters | 🟡 todo | LLM-001 |
| [LLM-004](LLM-004.md) | Embedding service adapter | 🟡 todo | LLM-001 |

## Wave 5: Project Context

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [CTX-001](CTX-001.md) | Qdrant integration | 🟡 todo | CORE-006, LLM-004 |
| [CTX-002](CTX-002.md) | index_repo tool | 🟡 todo | CTX-001, REPO-001, REPO-002 |
| [CTX-003](CTX-003.md) | get_project_context tool | 🟡 todo | CTX-001, CTX-002 |
| [CTX-004](CTX-004.md) | Issue tracking tools | 🟡 todo | CTX-001, SETUP-003 |
| [CTX-005](CTX-005.md) | Context bundle generation | 🟡 todo | CTX-003 |

## Wave 6: Cross-Repo Intelligence

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [XREPO-001](XREPO-001.md) | Global search | 🟡 todo | CTX-002 |
| [XREPO-002](XREPO-002.md) | Repo relationships | 🟡 todo | CORE-004, SETUP-003 |
| [XREPO-003](XREPO-003.md) | Project landscape and architecture maps | 🟡 todo | XREPO-001, XREPO-002 |

## Wave 7: Distributed LLM Routing

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [SCHED-001](SCHED-001.md) | Task classification | 🟡 todo | CORE-006 |
| [SCHED-002](SCHED-002.md) | Scheduler and routing engine | 🟡 todo | SCHED-001, CORE-006 |

## Wave 8: Observability

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [OBS-001](OBS-001.md) | Task history system | 🟡 todo | SETUP-003, SETUP-004 |
| [OBS-002](OBS-002.md) | History query tools | 🟡 todo | OBS-001 |
| [OBS-003](OBS-003.md) | Issue timeline | 🟡 todo | CTX-004, OBS-001 |

## Wave 9: Public Edge

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [EDGE-001](EDGE-001.md) | Cloudflare Tunnel integration | 🟡 todo | SETUP-002 |

## Wave 10: Polish

| ID | Title | Status | Depends On |
|----|-------|--------|------------|
| [POLISH-001](POLISH-001.md) | Error handling hardening | 🔴 blocked | CORE-007, REPO-001, LLM-001, CTX-003 |
| [POLISH-002](POLISH-002.md) | End-to-end integration tests | 🔴 blocked | POLISH-001 |
| [POLISH-003](POLISH-003.md) | API and MCP tool documentation | 🔴 blocked | POLISH-002 |
| [POLISH-004](POLISH-004.md) | Scheduled indexing | 🔴 blocked | CTX-002 |

---

## Dependency Graph (Critical Path)

```
SETUP-001 ──┬── SETUP-002 ──┬── SETUP-004 ── CORE-007
            │               │
            │               ├── CORE-001 ──┬── CORE-003 ──┬── REPO-001..004
            │               │              │              ├── WRITE-001
            │               │              │              └── LLM-001 ──┬── LLM-002..004
            │               │              │                            └── CTX-001 ── CTX-002 ── CTX-003 ── CTX-005
            │               │              ├── CORE-004
            │               │              ├── CORE-005
            │               │              └── CORE-006 ── SCHED-001 ── SCHED-002
            │               │
            │               └── EDGE-001
            │
            ├── SETUP-003 ──┘
            ├── SETUP-005
            └── CORE-002 ───┘
```

## Ready to Start (no unmet dependencies)

- **SETUP-001**: Project skeleton and dependencies
