# Implementation Plan: FIX-013 - Cloudflare Tunnel Runtime Management

## 1. Scope

Implement the runtime management of Cloudflare Tunnel (cloudflared) process from within the GPTTalker hub's lifespan, including subprocess management, health monitoring, systemd detection, and graceful shutdown.

## 2. Files and Systems Affected

### New Files to Create
- `src/hub/services/tunnel_manager.py` — Core tunnel subprocess manager with health monitoring

### Files to Modify
- `src/hub/lifespan.py` — Integrate tunnel manager startup/shutdown
- `src/hub/config.py` — Add tunnel-specific config fields
- `docs/ops/cloudflare-tunnel.md` — Update documentation

## 3. Implementation Steps

### Step 1: Extend HubConfig with tunnel management settings

Add new configuration fields in `src/hub/config.py`:
- `cloudflare_tunnel_health_check_interval: int = 30`
- `cloudflare_tunnel_restart_delay: int = 5`
- `cloudflare_tunnel_max_restarts: int = 5`

### Step 2: Create TunnelManager service

Create `src/hub/services/tunnel_manager.py` with:

1. **TunnelManager class**:
   - `start()` — Start cloudflared subprocess if enabled
   - `stop()` — Gracefully terminate subprocess
   - `health_check()` — Verify tunnel is running
   - `_monitor_loop()` — Background task for health monitoring
   - `_restart()` — Attempt restart on failure

2. **Systemd detection logic**:
   - Check if cloudflared process already running via `pgrep cloudflared`
   - Query systemd via `systemctl is-active cloudflared`
   - If external process detected, skip subprocess management

3. **Subprocess management**:
   - Use `asyncio.create_subprocess_exec`
   - Pass token via environment variable `CLOUDFLARE_TUNNEL_TOKEN`
   - Graceful shutdown with SIGTERM, fallback to SIGKILL

4. **Health monitoring**:
   - Background asyncio task runs health checks at configured interval
   - On failure: attempt restart up to `max_restarts` times
   - Fail-open: log failures but continue hub operation

### Step 3: Integrate with lifespan

Modify `src/hub/lifespan.py`:
- Initialize TunnelManager in startup phase
- Store reference in `app.state.tunnel_manager`
- Call `await tunnel_manager.stop()` in shutdown phase

### Step 4: Token redaction

Existing `SENSITIVE_PATTERNS` in logging.py already includes "token". Verify redaction works.

### Step 5: Update documentation

Update `docs/ops/cloudflare-tunnel.md` to accurately reflect:
- Automatic cloudflared startup behavior
- Systemd detection behavior
- New environment variables
- Troubleshooting section

## 4. Acceptance Criteria

| Criterion | Verification |
|-----------|--------------|
| Hub lifespan starts cloudflared subprocess when enabled | Start hub, verify cloudflared process |
| Systemd detection skips subprocess management | Start cloudflared via systemd, verify hub skips |
| Health monitoring with automatic restart | Kill cloudflared, verify restart |
| Graceful shutdown terminates subprocess | Stop hub, verify cloudflared terminated |
| Tokens read from env vars only | Code review: no hardcoded tokens |
| Docs accurately reflect behavior | Read docs, verify accuracy |
| Structured logs redact tunnel tokens | Check logs, verify token redacted |

## 5. Risks

- Network-dependent health check: Check process liveness first
- Token in process environment: Standard practice for cloudflared

## 6. Blocker Checklist

- [x] No blocking decisions remain
- [x] cloudflared installation assumed
- [x] Permissions assumed