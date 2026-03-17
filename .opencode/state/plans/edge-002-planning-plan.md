# Planning: EDGE-002

## Ticket
- **ID**: EDGE-002
- **Title**: Node registration bootstrap and operator config docs
- **Wave**: 5
- **Lane**: edge

## Summary
Add the operator-facing bootstrap path for bringing nodes online, registering them, and documenting the edge and connectivity setup.

## Acceptance Criteria
1. Node bootstrap flow is explicit
2. Operator config requirements are documented
3. Registration flow aligns with the node registry and public-edge setup

## Dependencies
- CORE-001 (Node registry and node health model)
- CORE-003 (Node agent service skeleton)
- EDGE-001 (Cloudflare Tunnel integration)

## Analysis

### Background
GPTTalker uses a node-agent architecture where each managed machine runs a lightweight agent. Operators need clear documentation for:
1. Setting up the node agent on a new machine
2. Registering the node with the hub
3. Configuring connectivity (Tailscale)
4. Verifying the node is healthy

### What's Needed
1. **Node Setup Guide** - Step-by-step for setting up node agent
2. **Registration Flow** - How to register nodes with the hub
3. **Configuration Reference** - All environment variables needed
4. **Health Verification** - How to verify node is working

### Implementation Plan
1. Create `docs/ops/node-setup.md` - Node agent installation guide
2. Create `docs/ops/node-registration.md` - Node registration guide
3. Update `docs/ops/cloudflare-tunnel.md` - Link from EDGE-001 if needed

## Validation
- Documentation completeness
- Configuration reference accuracy
