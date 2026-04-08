# Planning Artifact: EDGE-003 — Replace Cloudflare public edge with ngrok runtime and config

## Source Ticket
- EDGE-001 (Cloudflare Tunnel integration — superseded by March 31 ngrok pivot)

## Current State Analysis

### Runtime surfaces — already migrated ✅
| File | ngrok state |
|------|-------------|
| `src/hub/config.py` | `ngrok_auth_token`, `ngrok_api_key`, `ngrok_config_path`, `ngrok_region`, `ngrok_log_level` fields present. No Cloudflare-specific fields. |
| `src/hub/services/tunnel_manager.py` | `TunnelManager` class manages ngrok subprocess: start, health monitoring, restart on failure, graceful shutdown, systemd detection, token redaction in logs. |
| `src/hub/lifespan.py` | `TunnelManager` initialized during hub startup. |
| `src/hub/services/__init__.py` | **`TunnelManager` not exported** — single remaining gap. |
| `docs/ops/ngrok.md` | Canonical operator guide for ngrok setup. |
| `docs/ops/cloudflare-tunnel.md` | Marked as historical; superseded. |

### Single remaining gap
`TunnelManager` is implemented but not re-exported from `src/hub/services/__init__.py`, preventing `from src.hub.services import TunnelManager` from working.

---

## Acceptance Criteria Status

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 1. Hub config exposes ngrok-specific settings | ✅ MET | `config.py` has ngrok fields; no CF fields |
| 2. Hub startup launches/detects ngrok | ✅ MET | `lifespan.py` initializes `TunnelManager` for ngrok |
| 3. Operator docs describe ngrok | ✅ MET | `docs/ops/ngrok.md` is canonical guide |
| 4. Validation of ngrok health/command | ✅ MET | `TunnelManager` has health monitoring, restart, log redaction |

---

## Implementation Plan

**Single step**: Add `TunnelManager` to `src/hub/services/__init__.py` exports.

### Files to modify
- `src/hub/services/__init__.py` — add `TunnelManager` to `__all__` and import

### Validation commands
1. `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.services import TunnelManager"` — exit 0
2. `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"` — exit 0
3. `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile src/hub/services/tunnel_manager.py` — exit 0
4. `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/services/__init__.py` — exit 0

---

## Decision Blockers
None. The ngrok migration is already complete in all runtime surfaces. The single missing export is a trivial fix.

## Notes
- The hard migration work was already done in FIX-013 and earlier EXEC wave tickets.
- EDGE-004 (ticket lineage reconciliation) depends on EDGE-003 completing first.
