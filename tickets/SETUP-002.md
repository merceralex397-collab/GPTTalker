# SETUP-002: Hub FastAPI application skeleton

## Summary

Create the main FastAPI application for the GPTTalker hub server. This includes the app factory with startup/shutdown lifecycle hooks, a health check endpoint, configuration loading from a YAML or TOML config file, and a uvicorn entrypoint for running the server. This skeleton becomes the foundation for all hub-side MCP tools and API endpoints.

## Stage

planning

## Status

todo

## Depends On

- SETUP-001

## Acceptance Criteria

- [ ] FastAPI app factory function exists at src/hub/app.py
- [ ] Startup hook logs server start and initializes shared resources
- [ ] Shutdown hook cleans up resources gracefully
- [ ] GET /health returns {"status": "ok", "version": "..."} with 200
- [ ] Configuration loads from config.toml or config.yaml with sensible defaults
- [ ] Config model defined with Pydantic for validation
- [ ] uvicorn entrypoint exists (python -m hub or hub CLI)
- [ ] Server starts and responds to health check

## Artifacts

- None yet

## Notes

- Config should support: host, port, db_path, log_level, tailscale settings
- Use lifespan context manager (modern FastAPI pattern) over on_event decorators
- Keep CORS and middleware minimal until needed
