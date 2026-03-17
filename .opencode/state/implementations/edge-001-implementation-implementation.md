# Implementation: EDGE-001

## Summary
Added Cloudflare Tunnel configuration and documentation for public-edge access.

## Changes Made

### Modified Files
1. **src/hub/config.py**:
   - Added Cloudflare Tunnel settings to HubConfig:
     - cloudflare_tunnel_enabled (bool, default false)
     - cloudflare_tunnel_token (str | None)
     - cloudflare_tunnel_hostname (str | None)  
     - cloudflare_tunnel_url (str, default http://localhost:8000)

### New Files
1. **docs/ops/cloudflare-tunnel.md**:
   - Complete setup documentation for Cloudflare Tunnel
   - Prerequisites, step-by-step instructions
   - Environment variable configuration
   - Security considerations
   - Troubleshooting guide

## Acceptance Criteria
- Tunnel configuration owner is explicit ✓
- HTTPS public-edge boundary is documented in code and config ✓
- Security constraints remain aligned with the brief ✓
