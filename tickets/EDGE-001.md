# EDGE-001: Cloudflare Tunnel integration

## Summary

Document and implement the Cloudflare Tunnel configuration for exposing the GPTTalker hub to the public internet securely. The hub runs on a private Tailscale network; Cloudflare Tunnel provides the public edge with HTTPS enforcement, DDoS protection, and access control. Include configuration guides, setup scripts, and the public/private separation architecture.

## Stage

planning

## Status

todo

## Depends On

- SETUP-002

## Acceptance Criteria

- [ ] Cloudflare Tunnel configuration template (cloudflared config)
- [ ] Setup script or guide for tunnel installation and configuration
- [ ] Hub origin binding: tunnel connects to localhost or Tailscale IP only
- [ ] HTTPS enforcement: all public traffic over TLS
- [ ] Public → private separation: only MCP endpoints exposed publicly
- [ ] Internal admin/management endpoints not exposed through tunnel
- [ ] Health check endpoint accessible through tunnel
- [ ] Authentication recommendation: Cloudflare Access or API token validation
- [ ] Deployment guide with step-by-step instructions
- [ ] Network architecture diagram (text/mermaid format)

## Artifacts

- None yet

## Notes

- Cloudflare Tunnel (cloudflared) creates an outbound-only connection — no inbound ports needed
- Consider Cloudflare Access for additional authentication layer
- Hub should bind to 127.0.0.1 or Tailscale IP — never 0.0.0.0 in production
- MCP endpoint is the only thing that needs public exposure
