# Planning: EDGE-001

## Ticket
- **ID**: EDGE-001
- **Title**: Cloudflare Tunnel integration and public-edge config
- **Wave**: 5
- **Lane**: edge

## Summary
Define and implement the public-edge path through Cloudflare Tunnel so ChatGPT can reach the hub over HTTPS without exposing inbound ports.

## Acceptance Criteria
1. Tunnel configuration owner is explicit
2. HTTPS public-edge boundary is documented in code and config
3. Security constraints remain aligned with the brief

## Dependencies
- SETUP-004 (FastAPI hub app shell)
- CORE-005 (Policy engine and normalized path validation)

## Analysis

### Background
Cloudflare Tunnel provides a way to expose a local service to the internet without:
- Opening inbound ports on the firewall
- Managing SSL certificates
- Direct exposure of the service IP

The hub will run internally and tunnel traffic through Cloudflare's edge network.

### What's Needed
1. **Hub Configuration** - Add Cloudflare Tunnel settings to config
2. **Tunnel Setup Script** - Documentation for creating/configuring tunnel
3. **Startup Integration** - Optional: integrate tunnel start with hub startup
4. **Security Documentation** - Document security constraints

### Implementation Plan
1. Create `src/hub/config/cloudflare.py` with tunnel configuration
2. Update hub config to include tunnel settings
3. Create documentation for tunnel setup (`docs/ops/cloudflare-tunnel.md`)
4. Add tunnel health check or status endpoint

### Configuration Structure
```python
class CloudflareConfig:
    tunnel_token: str | None = None  # Tunnel authentication
    tunnel_hostname: str | None = None  # Public hostname
    tunnel_url: str | None = None  # Local hub URL (default: http://localhost:8000)
```

## Validation
- Configuration schema validation
- Documentation completeness
