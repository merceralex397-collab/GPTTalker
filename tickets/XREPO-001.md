# XREPO-001: Global search

## Summary

Implement cross-repository search tools that allow ChatGPT to search across all indexed repositories simultaneously. Provide search_across_repos for text/code search and search_global_context for semantic search across all Qdrant collections. Combine keyword and semantic results for comprehensive cross-project discovery.

## Stage

planning

## Status

todo

## Depends On

- CTX-002

## Acceptance Criteria

- [ ] search_across_repos MCP tool: text search across multiple repos
- [ ] search_global_context MCP tool: semantic search across all Qdrant collections
- [ ] Cross-collection Qdrant queries with repo metadata in results
- [ ] Combined keyword + semantic result ranking
- [ ] Results grouped by repository with relevance scores
- [ ] Configurable repo filter (search specific subset or all)
- [ ] Result limit and pagination support
- [ ] Response includes: results, repos_searched, total_matches
- [ ] Performance: parallel queries across repos/collections
- [ ] Unit tests with mocked multi-repo data

## Artifacts

- None yet

## Notes

- search_across_repos fans out to node agents for ripgrep (parallel)
- search_global_context queries Qdrant global collection + per-repo collections
- Consider capping concurrent node queries to prevent overwhelming the network
- Results should clearly identify which repo each result comes from
