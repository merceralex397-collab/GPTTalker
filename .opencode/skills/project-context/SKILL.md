---
name: project-context
description: Load the local source-of-truth docs for GPTTalker before planning, implementing, reviewing, or handing off work.
---

# Project Context

Before reading anything else, call `skill_ping` with `skill_id: "project-context"` and `scope: "project"`.

## What this project is

GPTTalker is a scaffolded Python + FastAPI MCP hub for safe multi-machine development workflows. The repo is currently a planning and execution scaffold; runtime implementation work starts from the backlog.

## Read these first

1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `mcp_spec_pack/00-overview/00_project_brief.md`
5. `docs/process/workflow.md`
6. `tickets/manifest.json`
7. `tickets/BOARD.md`

## When to read deeper

- use `mcp_spec_pack/01-hard-specs/` for detailed tool and architecture expectations
- use `mcp_spec_pack/02-proposals/` when a ticket touches an accepted proposal or an intentionally deferred choice
- use `.opencode/meta/bootstrap-provenance.json` when process-version or retrofit history matters
