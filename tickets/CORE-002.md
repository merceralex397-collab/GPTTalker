# CORE-002: Node agent service skeleton

## Summary

Create the standalone FastAPI service that runs on each managed machine in the GPTTalker network. This node agent exposes a health endpoint, advertises its capabilities to the hub, and loads local configuration for repo paths, write roots, and available LLM services. The node agent is the execution layer — it performs local operations on behalf of the hub.

## Stage

planning

## Status

todo

## Depends On

- SETUP-001

## Acceptance Criteria

- [ ] Node agent FastAPI app at src/node_agent/app.py
- [ ] GET /health returns {"status": "ok", "node_name": "...", "capabilities": [...]}
- [ ] Configuration loaded from local config file (node-config.toml)
- [ ] Config includes: node_name, hub_url, repo_paths, write_roots, llm_services
- [ ] Pydantic config model with validation
- [ ] Uvicorn entrypoint for standalone operation
- [ ] Startup logs node name and configured capabilities
- [ ] Graceful shutdown handling

## Artifacts

- None yet

## Notes

- Node agent runs independently — it doesn't import hub code
- Shared models/schemas live in src/shared/ for both to import
- Each node agent instance serves one machine
- Consider auto-registration with hub on startup
