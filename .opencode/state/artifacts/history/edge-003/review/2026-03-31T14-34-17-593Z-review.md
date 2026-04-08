# Code Review: EDGE-003 — Replace Cloudflare public edge with ngrok runtime and config

## Decision: APPROVED

## Rationale

The implementation correctly addresses the single remaining gap in the ngrok migration:

**Fix**: Added `TunnelManager` to `src/hub/services/__init__.py`:
- Import: `from .tunnel_manager import TunnelManager`
- Export: `"TunnelManager"` in `__all__`

**Verification**:
1. ✅ `from src.hub.services import TunnelManager` — exit 0
2. ✅ `from src.hub.main import app` — exit 0  
3. ✅ `py_compile src/hub/services/tunnel_manager.py` — exit 0
4. ✅ `ruff check src/hub/services/__init__.py` — exit 0

**Acceptance criteria mapping**:
- AC-1 (ngrok config fields): Already present in `config.py` — ✅
- AC-2 (ngrok runtime management): Already implemented via `TunnelManager` in `lifespan.py` — ✅
- AC-3 (ngrok operator docs): Already present at `docs/ops/ngrok.md` — ✅
- AC-4 (ngrok health validation): Already implemented in `TunnelManager` — ✅

**No security regressions**. No widened trust boundaries. No path validation changes.

## Non-blocking Observations
None — the fix is a single correct export addition.
