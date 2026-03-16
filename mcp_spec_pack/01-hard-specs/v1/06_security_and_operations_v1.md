# V1 Hard Spec — Security and Operations

## Simple explanation

This is the safety layer.

In plain terms:
- the system should be useful, but not reckless
- it should know which machines exist, which repos are allowed, and where writing is permitted
- it should keep logs and survive restarts
- it should fail safely rather than guessing

## Status

Hard-set specification.

## Goals

Define V1 operational and security rules.

## Requirements

- The hub SHALL keep persistent config and history.
- The system SHALL support Tailscale for private internal connectivity.
- The ChatGPT-facing MCP edge SHALL be reachable over HTTPS.
- The system SHALL support node registry, repo registry, and write-target registry.
- The system SHALL keep task history and operational logs.
- The system SHALL fail closed on unknown targets.

## Architecture

Operational domains:
1. connectivity
2. identity and auth
3. registry management
4. logging
5. persistence
6. health checks

Required registries:
- nodes
- repos
- write roots
- LLM services
- indexing status

## Interfaces and behavior

Operational behaviors:
- health check each registered node
- verify service status for LLM backends
- maintain task history records
- allow export of logs/history for audit
- support startup recovery from persistent storage

Suggested records:
- task id
- request type
- node
- repo/service
- start/end time
- result
- error code

## Failure modes

- Lost Tailscale connectivity: mark internal actions unavailable.
- Public edge down: ChatGPT cannot connect, but internal state remains intact.
- Context store unavailable: degrade context features only.
- History store corruption: restore from backups if configured.

## Security considerations

Security baseline:
- default deny for unknown nodes and repos
- no unrestricted shell
- no arbitrary path access
- redact secrets in logs where practical
- separate secrets/config from repo content
- use HTTPS for public edge
- use Tailscale internally

## Implementation notes

For native ChatGPT MCP use, plan for:
- public HTTPS edge via tunnel or proxy
- internal-only hub origin bound to localhost or Tailscale
- strong separation between public ingress and internal machine control
