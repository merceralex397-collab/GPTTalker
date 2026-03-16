# XREPO-002: Repo relationships

## Summary

Implement repository relationship tracking and the list_related_repos MCP tool. Allow registration of relationships between repositories (dependency, ownership, related, fork) and provide tools for ChatGPT to understand how projects connect to each other across the development environment.

## Stage

planning

## Status

todo

## Depends On

- CORE-004
- SETUP-003

## Acceptance Criteria

- [ ] Repo relationship model: id, source_repo_id, target_repo_id, relationship_type, metadata, created_at
- [ ] Relationship types: depends_on, dependency_of, related, fork_of, monorepo_member
- [ ] Register relationship endpoint
- [ ] list_related_repos MCP tool: given a repo alias, return related repos with relationship types
- [ ] Bidirectional relationship queries (A depends on B → B is dependency of A)
- [ ] Relationship metadata: version constraint, shared owner, etc.
- [ ] Prevent duplicate relationships
- [ ] Unit tests for relationship CRUD and queries

## Artifacts

- None yet

## Notes

- Relationships can be manually registered or auto-detected from package files
- Consider auto-detection: scan package.json, requirements.txt, go.mod for cross-repo deps
- Bidirectional queries are important: "what depends on this repo?" and "what does this repo depend on?"
