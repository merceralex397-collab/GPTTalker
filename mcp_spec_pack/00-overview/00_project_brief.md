# Project Brief — Lightweight MCP Hub for Multi-Machine Development

## Plain-English summary

This project is a lightweight **MCP hub** that lets ChatGPT safely interact with your development environment.

In simple terms, it is a **middleman service**:

- ChatGPT asks for something
- the MCP hub checks whether that action is allowed
- the MCP hub then talks to the right machine, repo, or LLM
- the MCP hub returns the result

The system is designed for a setup where:

- you have multiple machines
- your repos live on different machines
- your LLMs may run on a different machine from the MCP hub
- everything is linked through Tailscale

## What it should do

### 1. Inspect repository
ChatGPT can inspect approved Git repositories.

That means it can:

- list files and folders
- read selected files
- search code and docs
- view branch name, status, and recent commits
- build project summaries from what it reads

This is primarily **read-only** in the first version.

### 2. Talk to LLM
ChatGPT can send prompts to an approved LLM service or coding agent.

That means it can:

- ask a local model questions about a repo
- send work to an OpenCode server
- use a small helper model for quick classification, routing, or embedding tasks
- collect the answer and continue reasoning

### 3. Send markdown
ChatGPT can write markdown files into approved locations.

That means it can:

- create plans
- create specs
- create issue summaries
- write architecture notes
- drop docs into the right repo folder

### 4. Route work across multiple machines
One machine hosts the MCP hub, but the hub can route work to other machines over Tailscale.

That means it can:

- inspect a repo on machine A
- talk to an LLM on machine B
- write markdown into a repo on machine C

## What “MCP” means in plain terms

MCP is just a standard way for ChatGPT to use tools safely.

Think of it like this:

- **ChatGPT** = the planner
- **MCP hub** = the control desk
- **your machines and tools** = the things being controlled

## Hard-set system goals

1. Lightweight enough to run on an older laptop.
2. Safe enough to avoid unrestricted shell access.
3. Structured enough to support many repos and machines.
4. Flexible enough to support both node-agent and SSH-based designs.
5. Strong project context support for understanding a repo over time.
6. Designed around mostly-read workflows, with tightly controlled markdown writing.

## Recommended first deployment shape

- MCP hub on an old laptop
- main LLM on a different machine
- repos spread across multiple machines
- Tailscale used for private connectivity between devices
- public HTTPS edge or tunnel only for ChatGPT-to-hub connectivity
- all internal machine-to-machine traffic stays on Tailscale

## Non-goals for V1

These are intentionally excluded from the first hard-set version:

- unrestricted shell execution
- arbitrary file writes anywhere on the system
- autonomous code editing without review
- direct git commit / push actions
- wide-open remote control of every machine

## Deliverables in this pack

This pack contains:

- hard-set V1 specs
- hard-set V2 specs
- proposal specs for architecture options
- proposal specs for vector DB and project context
- proposal specs for distributed LLM execution
- proposal specs for node-agent and SSH-only designs
- simple explanations alongside more formal RFC-style sections
