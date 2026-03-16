# V2 Hard Spec — Cross-Repo Intelligence

## Simple explanation

This is for when the system needs to understand several repos together.

In plain terms:
- which repo owns what
- which docs mention the same system
- where a recurring bug crosses boundaries
- how pieces fit together across projects

## Status

Hard-set specification.

## Goals

Support project understanding beyond single-repo boundaries.

## Requirements

- V2 SHALL support global project registry.
- V2 SHALL support cross-repo semantic retrieval.
- V2 SHALL support relationship metadata between repos.
- V2 SHALL support cross-repo issue references.

## Architecture

Key layers:
- global repo registry
- shared metadata
- cross-repo search
- relationship graph

## Interfaces and behavior

Required tools:
- `search_across_repos(query)`
- `list_related_repos(repo)`
- `get_project_landscape()`

## Failure modes

- Missing metadata: return partial cross-repo map.
- Stale relationships: timestamp clearly and degrade confidence.

## Security considerations

Cross-repo visibility should be governed carefully if some repos are more sensitive than others.

## Implementation notes

This becomes especially valuable if you keep plans, specs, tools, and experiments in separate repos.
