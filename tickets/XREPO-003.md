# XREPO-003: Project landscape and architecture maps

## Summary

Implement the get_project_landscape and get_architecture_map MCP tools that provide ChatGPT with high-level views of the entire development environment. The landscape tool shows all projects with summaries and relationships. The architecture map generates module/service/dependency graphs for individual or cross-repo systems.

## Stage

planning

## Status

todo

## Depends On

- XREPO-001
- XREPO-002

## Acceptance Criteria

- [ ] get_project_landscape MCP tool: overview of all registered repos
- [ ] Landscape includes: repo alias, node, language, summary, status, relationship count
- [ ] get_architecture_map MCP tool: dependency/module graph for a repo or set of repos
- [ ] Architecture map includes: modules, services, dependencies, entry points
- [ ] Graph output in text format (mermaid-compatible or ASCII)
- [ ] Cross-repo dependency visualization
- [ ] Configurable detail level: summary, standard, detailed
- [ ] Results sourced from Qdrant context + repo metadata + relationships
- [ ] Unit tests with sample multi-repo data

## Artifacts

- None yet

## Notes

- Landscape is a "dashboard" view for ChatGPT to understand the full environment
- Architecture map generation may use helper LLM for summarization
- Mermaid format is useful as ChatGPT can render it in conversations
- Consider caching landscape/architecture data with TTL
