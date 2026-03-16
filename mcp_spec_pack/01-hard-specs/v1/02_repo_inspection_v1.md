# V1 Hard Spec — Repository Inspection

## Simple explanation

This is the part that lets ChatGPT understand a repo without changing it.

In plain terms, it gives ChatGPT safe reading powers:
- see the file tree
- open files
- search for symbols or text
- understand branch status
- collect recent commit information

This is the foundation for planning, debugging, and documentation.

## Status

Hard-set specification.

## Goals

Provide strong, predictable read access to approved Git repositories.

## Requirements

- Repo inspection SHALL be read-only.
- Access SHALL be by repo alias, not arbitrary path.
- Inspection SHALL support:
  - tree listing
  - file reading
  - text search
  - git status
  - recent commits
- Large outputs SHALL be chunked or truncated with clear notices.
- Binary files SHALL be identified and not returned as raw text.

## Architecture

Inspection flow:
1. resolve node
2. resolve repo alias
3. confirm target path is within repo
4. execute read operation
5. normalize output
6. log result

Inspection sources:
- filesystem contents
- git metadata
- indexed summaries from context store

## Interfaces and behavior

Tool contracts:

### `list_repos(node)`
Returns registered repo aliases and metadata.

### `inspect_repo_tree(node, repo, path="")`
Returns immediate and optionally recursive tree views.

### `read_repo_file(node, repo, file_path)`
Returns text content plus metadata:
- size
- extension
- modified time
- truncation flag

### `search_repo(node, repo, query, mode="text")`
Supported search modes:
- text
- path
- symbol (best effort)

### `git_status(node, repo)`
Returns:
- branch
- dirty flag
- changed files summary
- ahead/behind if available
- recent commits

## Failure modes

- Missing repo alias: fail closed.
- Out-of-repo path traversal: fail closed.
- File too large: return partial view plus metadata.
- Non-text file: return metadata only.
- Git unavailable: return filesystem-only result and degraded git status.

## Security considerations

- Never expose unrestricted path reads.
- Normalize and validate all file paths.
- Do not expose secrets discovered in known secret paths without an explicit redaction policy.
- Consider redaction of `.env`, private keys, token stores, and credential files by default.

## Implementation notes

Recommended implementation:
- git CLI for status/commits
- ripgrep for search
- extension-based + heuristic text detection
- optional ignore rules for noisy generated folders

Suggested extras:
- file summary cache
- import graph extraction
- recent hot file detection
