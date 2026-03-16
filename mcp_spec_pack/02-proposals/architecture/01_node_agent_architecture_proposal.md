# Proposal — Node Agent Architecture

## Simple explanation

A node agent is a small helper program running on each machine.

In plain terms:
- every machine gets its own local helper
- the hub talks to that helper over Tailscale
- the helper knows how to inspect repos, write files, and talk to local LLM services on that machine

This is usually the cleanest design when you have many machines doing different jobs.

## Status

Proposal document.

## Options

### Option summary
A lightweight agent runs on each managed machine.

### What it can do
- read local repos
- write markdown to local approved folders
- start or talk to local services
- report health
- expose local capabilities in a clean way

### Advantages
- Clean separation per machine.
- Easier local path handling because each machine understands its own filesystem.
- Better fit for talking to local services like OpenCode or a local model.
- Faster repeated access because the agent stays running.
- Easier health checks and telemetry.
- Easier future scaling.

### Downsides
- You have to install and maintain software on every machine.
- Version drift can happen if agents are not updated consistently.
- More moving pieces.

### Best use cases
- Many machines with different roles.
- Repos scattered across devices.
- Local services on those devices.
- Need for stronger observability and control.

### Proposed shape
- hub on old laptop
- tiny agent on each managed machine
- public HTTPS edge only at the hub
- Tailscale for all hub-to-agent traffic

## Recommendation

Recommended if you expect this system to grow and remain in regular use.
