# GPTTalker — START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## Project

GPTTalker

## Current State

The repo has completed waves 0-6 (32 original tickets) but post-implementation review has identified critical blockers, functional defects, and incomplete implementations that prevent end-to-end operation. 17 remediation tickets (FIX-001 through FIX-017) have been created across waves 7-8.

## Process Contract

- process_version: 2
- parallel_mode: parallel-lanes
- pending_process_verification: false
- process_changed_at: 2026-03-16T10:59:52.052Z
- process_note: Full retrofit rewrite from updated Scafforge templates using mcp_spec_pack as the preserved reference source.
- process_state: Remediation wave active. 17 FIX tickets pending.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/BOARD.md
6. tickets/manifest.json

## Current Ticket

FIX-001: Fix walrus operator syntax error in opencode.py

## Validation Status

Original wave tickets completed (waves 0-6):
- Wave 0: SETUP-001 through SETUP-005 (done)
- Wave 1: CORE-001 through CORE-006 (done)
- Wave 2: REPO-001, REPO-002, REPO-003, WRITE-001, LLM-001 (done)
- Wave 3: LLM-002, LLM-003, CTX-001, CTX-002, CTX-003, CTX-004 (done)
- Wave 4: XREPO-001, XREPO-002, XREPO-003, SCHED-001, SCHED-002 (done)
- Wave 5: OBS-001, OBS-002, EDGE-001, EDGE-002 (done)
- Wave 6: POLISH-001, POLISH-002, POLISH-003 (done)

Remediation tickets (waves 7-8):
- Wave 7 blockers: FIX-001 through FIX-005 (todo) — syntax error, type error, async wiring, SQLite persistence, logger/config
- Wave 7 defects: FIX-006 through FIX-010 (todo) — tool registration, search parser, git_status, write_markdown, observability
- Wave 8 completion: FIX-011 through FIX-013 (todo) — aggregation stubs, cross-repo metrics, cloudflare runtime
- Wave 8 hardening: FIX-014 through FIX-017 (todo) — placeholder tests, UUID/packaging, security, cleanup

## Known Risks

- Hub cannot start due to SyntaxError in opencode.py (FIX-001)
- Node agent cannot import due to Depends[] TypeError (FIX-002)
- MCP endpoints non-functional in async context (FIX-003)
- SQLite writes may silently roll back (FIX-004)
- Repo search returns zero matches due to parser mismatch (FIX-007)
- read_repo_file handler exists but is not registered (FIX-006)
- Aggregation service and cross-repo landscape return empty/zero data (FIX-011, FIX-012)
- Cloudflare Tunnel has no runtime code despite docs claiming it (FIX-013)

## Next Action

Begin wave 7 remediation starting with FIX-001 (walrus operator syntax fix). FIX-001, FIX-002, FIX-004, FIX-005 have no dependencies and can be worked in parallel.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
