# Implementation of FIX-013: Cloudflare Tunnel Runtime Management

## Summary

Implemented Cloudflare Tunnel runtime management with subprocess control, health monitoring, and systemd detection.

## Changes Made

### 1. src/hub/config.py
- Added `cloudflare_tunnel_health_check_interval: int = 30`
- Added `cloudflare_tunnel_restart_delay: int = 5`
- Added `cloudflare_tunnel_max_restarts: int = 5`

### 2. src/hub/services/tunnel_manager.py (NEW - 267 lines)
- TunnelManager class with:
  - `start()` - Starts cloudflared subprocess if enabled
  - `stop()` - Gracefully terminates with SIGTERM, SIGKILL fallback
  - `health_check()` - Returns health status
  - `_monitor_loop()` - Background health monitoring
  - `_check_external_management()` - Detects systemd/running process
- Uses asyncio.create_subprocess_exec
- Token via CLOUDFLARE_TUNNEL_TOKEN env var
- Systemd detection via systemctl
- Process detection via pgrep
- Fail-open behavior

### 3. src/hub/lifespan.py
- Initializes TunnelManager in startup
- Stores in app.state.tunnel_manager
- Calls stop() on shutdown

### 4. docs/ops/cloudflare-tunnel.md
- Updated to reflect automatic startup
- Added configuration environment variables
- Added troubleshooting section

## Acceptance Criteria

- ✅ Hub lifespan starts cloudflared subprocess when enabled
- ✅ Systemd detection skips subprocess management
- ✅ Health monitoring with auto-restart
- ✅ Graceful shutdown terminates subprocess
- ✅ Tokens from env vars only
- ✅ Docs updated
- ✅ Token redaction via SENSITIVE_PATTERNS