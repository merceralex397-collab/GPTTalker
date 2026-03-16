# V1 Hard Spec — Project Context

## Simple explanation

This is the part that helps the system remember what a project is, what problems it has had, and what important knowledge has already been found.

In plain terms:
- instead of reading the whole repo every time
- the system builds a searchable memory of the project
- that memory can include code summaries, docs, known issues, architecture notes, and history

A vector database is one way to store “semantic” search data. That means it helps find things by meaning, not only exact wording.

## Status

Hard-set specification.

## Goals

Create a persistent project-context system for approved repos.

## Requirements

- V1 SHALL persist project knowledge across restarts.
- V1 SHALL support per-repo indexing.
- V1 SHALL support a global metadata layer for cross-project records.
- V1 SHALL store:
  - repo summaries
  - file summaries
  - issue records
  - generated plans/specs
  - embedding-based retrieval records
- V1 SHALL support manual reindexing.
- V1 SHOULD support write-triggered reindexing for generated markdown.

## Architecture

V1 context model:
1. structured store
   - repo registry
   - issue registry
   - task history
   - summary records
2. vector index
   - chunks from docs and selected code/context
3. retrieval layer
   - keyword + semantic retrieval
4. summary layer
   - produces compact context bundles for ChatGPT

## Interfaces and behavior

Required tools:

### `index_repo(node, repo)`
Build or refresh project context.

### `get_project_context(node, repo, query=None)`
Returns compact project context:
- project summary
- architecture summary
- key files
- recent docs
- relevant issue notes

### `list_known_issues(node, repo)`
Returns known issue records.

### `record_issue(node, repo, title, summary, severity, evidence=None)`
Optional manual issue recording.

Context sources in V1:
- markdown docs
- readme files
- selected source code summaries
- generated plans/specs
- issue markdown files
- recent commit messages (best effort)

## Failure modes

- Indexing failure: preserve prior context and mark refresh failed.
- Embedding service unavailable: structured records remain available.
- Repo moved or deleted: mark stale and surface warning.
- Overly large repo: allow staged or partial indexing.

## Security considerations

- Context storage may contain sensitive project knowledge.
- Restrict which files are indexed.
- Exclude secrets, build artifacts, caches, dependency folders, and token files.
- Ensure deletion workflows can remove indexed content if a repo is unregistered.

## Implementation notes

Recommended V1 implementation stance:
- hybrid context system:
  - structured DB for exact records
  - vector DB for semantic lookup
- this gives both reliability and meaning-based search

Recommended first-pass indexed sources:
- README and docs
- generated specs/plans
- issue logs
- code summaries rather than raw full-code embeddings for every file
