# GPTTalker — START HERE

> Derived restart surface. Canonical truth lives in `tickets/manifest.json` and `.opencode/state/workflow-state.json`.

---

## What This Repo Is

**GPTTalker** is a lightweight MCP hub that lets ChatGPT safely interact with a multi-machine development environment. ChatGPT sends requests via MCP; the hub enforces policy, routes work to the correct machine over Tailscale, and returns structured results.

Key capabilities: repo inspection, LLM bridging, markdown delivery, persistent project context (Qdrant), cross-repo intelligence, distributed model routing, full observability.

Stack: **Python 3.11+ · FastAPI · aiosqlite · Qdrant · httpx · Tailscale · Cloudflare Tunnel**
Model: `minimax-coding-plan/MiniMax-M2.7`

---

## Current State

**Post-repair. Development work is the active lane.**

The Scafforge managed-surface overhaul completed (cycle `2026-04-07T22:18:12Z`). All workflow tooling, plugins, skills, agents, and process docs have been refreshed. 65 of 67 tickets are `done`. Two remain:

| Ticket | Status | Summary |
|--------|--------|---------|
| `REMED-001` | todo | EXEC001 — hub cannot start: `RelationshipService` TYPE_CHECKING annotation NameError in `src/hub/dependencies.py` |
| `REMED-002` | todo | REF-003 (advisory) — `.opencode/node_modules/zod` false positive; no action required |

The workflow-state `active_ticket` is `EXEC-011` (stage: closeout / done). The correct next foreground ticket is `REMED-001`.

**Repair follow-on state**: The repair runner still records `project-skill-bootstrap` and `ticket-pack-builder` as `required_not_run` because the runner always refreshes skills from template (overwriting `stack-standards/SKILL.md`). Both stages are actually complete — completion artifacts are at `.opencode/state/artifacts/history/repair/*-completion.md` with cycle `2026-04-07T22:18:12Z`. **Do not re-run `run_managed_repair.py`** unless you immediately re-write `stack-standards/SKILL.md` afterward.

---

## Read In This Order

1. `README.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `docs/process/workflow.md`
5. `tickets/manifest.json`
6. `tickets/BOARD.md`
7. `.opencode/state/workflow-state.json`
8. `.opencode/meta/repair-follow-on-state.json`

---

## Current / Next Ticket

**REMED-001** — `todo`

Fix `NameError: name 'RelationshipService' is not defined` in `src/hub/dependencies.py`.

The function `get_relationship_service()` declares `-> RelationshipService:` as a return annotation, but `RelationshipService` is only imported inside a `TYPE_CHECKING` block. Change the annotation to `-> "RelationshipService":` (string annotation / PEP 484). Audit the rest of `src/hub/dependencies.py` for the same pattern.

Acceptance criteria:
- `uv run python -c "from src.hub.main import app"` exits 0
- `uv run pytest --tb=short -q` passes

---

## Generation Status

Scaffold: complete (Scafforge managed-surface repair cycle `2026-04-07T22:18:12Z`).
All 8 agent drift findings resolved. `stack-standards/SKILL.md` populated with project-specific content.

---

## Post-Generation Audit / Repair Status

Audit diagnosis packs: `diagnosis/20260407-213600` (initial), `diagnosis/20260407-214623` (post-repair), `diagnosis/20260407-221824` (latest).

Remaining audit findings after repair:
- **EXEC001** — hub import NameError (source-layer; tracked as REMED-001)
- **REF-003** — zod node_modules false positive (advisory; tracked as REMED-002)
- **CYCLE002** — repeated diagnosis packs without converging repair (expected; runner always rewrites SKILL.md)

`pending_process_verification: true` — workflow repair is complete but source-layer EXEC001 means the hub cannot start. Managed repair itself is not the blocker; REMED-001 is.

---

## Known Risks

- Hub service cannot start until REMED-001 (EXEC001) is fixed
- REMED-002 (REF-003 / zod) is advisory only — no action required
- `run_managed_repair.py` always replaces `stack-standards/SKILL.md` with a generic template; must be re-written after each repair runner invocation
- `record_repair_stage_completion.py` always fails with `missing_provenance` in this environment — use canonical completion artifacts instead
- Tailscale tailnet and Cloudflare Tunnel are external prerequisites not provisioned in this repo

---

## Next Action

**Fix REMED-001:**

```sh
# In src/hub/dependencies.py, find the return annotation on get_relationship_service
# Change:  ) -> RelationshipService:
# To:      ) -> "RelationshipService":
# Then verify:
uv run python -c "from src.hub.main import app; print('ok')"
uv run pytest --tb=short -q
```

Then close REMED-001 and proceed to the active development backlog (`SETUP-001` through `EXEC-014` are all done; continue from the next ready ticket).
