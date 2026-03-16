# V1 Hard Spec — System Architecture

## Simple explanation

V1 is the first solid version of the system. It is meant to be practical, safe, and small enough to run on an older laptop.

The basic shape is:

- ChatGPT talks to a remote MCP hub over HTTPS
- the hub routes internal work over Tailscale
- the hub can inspect repos, talk to approved LLM services, and write markdown files
- the system is mostly read-only except for controlled markdown output

This version is not trying to be fully autonomous. It is trying to be reliable.

## Status

Hard-set specification.

## Goals

1. Support one MCP hub instance.
2. Support multiple target machines.
3. Keep internal routing private over Tailscale.
4. Expose only a narrow toolset.
5. Make repo inspection and markdown writing dependable.
6. Keep operational complexity low enough for a solo developer deployment.

## Requirements

- The MCP hub SHALL run on a dedicated older laptop or equivalent always-on machine.
- The MCP hub SHALL expose a remote HTTPS endpoint suitable for ChatGPT MCP connectivity.
- Internal connectivity between the hub and managed machines SHALL use Tailscale.
- V1 SHALL support:
  - repo inspection
  - markdown delivery
  - LLM bridge calls
  - persistent project context storage
  - task history
- V1 SHALL be mostly read-only.
- V1 SHALL NOT include unrestricted shell execution.
- V1 SHALL NOT include git commit/push automation.
- V1 SHALL persist state across restarts.

## Architecture

Components:

1. **ChatGPT-facing edge**
   - Public HTTPS entry used by ChatGPT.
   - May be served by a tunnel or reverse proxy in front of the hub.

2. **MCP hub**
   - Central policy engine.
   - Tool exposure layer.
   - Request router.
   - Context manager.
   - History logger.

3. **Internal connectivity plane**
   - Tailscale tailnet used between the hub and managed machines.

4. **Managed targets**
   - Repo hosts.
   - LLM hosts.
   - Markdown write targets.

5. **Context store**
   - Persistent metadata store.
   - Vector index for semantic retrieval.
   - Structured records for issues, summaries, and history.

V1 deployment stance:
- one hub
- one main LLM machine
- many repo machines
- one public MCP edge
- all internal action stays private

## Interfaces and behavior

Required tool families:

- `list_nodes`
- `list_repos`
- `inspect_repo_tree`
- `read_repo_file`
- `search_repo`
- `git_status`
- `write_markdown`
- `chat_llm`
- `get_project_context`
- `list_known_issues`
- `list_task_history`

Behavior rules:
- All repo and file access SHALL be scoped to registered targets.
- All writes SHALL be limited to registered write roots.
- All LLM calls SHALL target approved services only.
- All tool calls SHALL be logged with timestamp, caller, target, outcome, and trace id.

## Failure modes

- If a node is offline, the hub SHALL return a structured node-unavailable error.
- If a repo alias is missing, the hub SHALL reject the request without fallback guessing.
- If the context store is degraded, repo inspection SHALL continue but context tools SHALL return degraded-mode responses.
- If a write path is invalid, the write SHALL fail closed.
- If an LLM backend times out, the request SHALL be marked failed and logged.

## Security considerations

- The public ChatGPT-facing edge SHALL be HTTPS.
- Internal machine-to-machine traffic SHALL use Tailscale.
- No unrestricted shell tool SHALL be exposed in V1.
- File writing SHALL use allowlisted roots and normalized relative paths.
- Hub logs SHALL omit raw secrets.
- Credentials SHALL be stored outside repo content and outside generated markdown.

## Implementation notes

Suggested implementation stack:
- Python + FastAPI for the hub
- SQLite/Postgres for structured records
- Qdrant/LanceDB/Chroma-class vector store
- ripgrep and git CLI for repo inspection
- HTTP adapters for OpenCode and other LLM services

Rationale:
- light enough for an old laptop
- simple enough to maintain
- flexible enough to grow into V2
