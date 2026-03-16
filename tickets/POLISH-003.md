# POLISH-003: API and MCP tool documentation

## Summary

Create complete documentation for all MCP tools, configuration options, and deployment procedures. Include a tool reference with input/output schemas, a configuration guide covering all config file options, and a deployment guide with step-by-step Tailscale + Cloudflare Tunnel setup instructions.

## Stage

planning

## Status

blocked

## Depends On

- POLISH-002

## Acceptance Criteria

- [ ] MCP tool reference: every tool documented with description, inputs, outputs, examples
- [ ] Tool reference includes error responses and edge cases
- [ ] Configuration guide: all config file options with defaults and descriptions
- [ ] Hub configuration reference (config.toml)
- [ ] Node agent configuration reference (node-config.toml)
- [ ] Deployment guide: prerequisites, installation, configuration, startup
- [ ] Tailscale setup: network creation, node joining, IP assignment
- [ ] Cloudflare Tunnel setup: tunnel creation, DNS, access policies
- [ ] Troubleshooting section: common issues and solutions
- [ ] Architecture overview with diagrams

## Artifacts

- None yet

## Notes

- Documentation should be in docs/ directory as markdown files
- Tool reference is the most important doc — ChatGPT users need to know what tools exist
- Consider generating tool reference from MCP tool definitions (schema → docs)
- Deployment guide should cover both single-machine dev and multi-machine production
