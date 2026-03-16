# CORE-006: LLM service registry

## Summary

Implement the LLM service registry that tracks all AI/ML services available across the GPTTalker network. Support multiple service kinds (coding_agent, general_llm, helper_llm, embedding_service) with per-service metadata including URL, capabilities, and authentication. This registry enables the hub to route AI requests to the appropriate backend.

## Stage

planning

## Status

todo

## Depends On

- CORE-001
- SETUP-003

## Acceptance Criteria

- [ ] LLMService model: id, node_id, alias (unique), kind, url, capabilities (JSON), auth_method, is_active, created_at
- [ ] Service kinds enum: coding_agent, general_llm, helper_llm, embedding_service
- [ ] Register LLM service with node ownership and URL validation
- [ ] list_llm_services MCP tool with kind filter
- [ ] Service health check via node agent
- [ ] Auth method support: none, api_key, bearer_token
- [ ] Auth credentials stored securely (not in plain text responses)
- [ ] Unregister/deactivate service endpoint
- [ ] Unit tests for CRUD and validation

## Artifacts

- None yet

## Notes

- Auth credentials should be stored encrypted or in a separate secrets store
- Capabilities examples: ["chat", "completion", "embedding", "code_edit"]
- Service URL is relative to the node (node agent proxies requests)
- Consider capability negotiation: hub queries what each service actually supports
