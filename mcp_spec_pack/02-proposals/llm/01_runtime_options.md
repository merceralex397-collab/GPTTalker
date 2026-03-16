# Proposal — LLM Runtime Options

## Simple explanation

This compares backends that could sit behind the MCP hub.

In plain terms:
- the runtime is the software that actually serves the AI model
- different runtimes suit different machines and workloads

## Status

Proposal document.

## Options

### Option A — OpenCode server
What it is:
- a coding-agent server designed around coding workflows

What it can do:
- session-based coding tasks
- code understanding and changes through its own model/provider setup

Advantages:
- directly aligned with coding-agent use
- good fit if the goal is “ChatGPT orchestrates a coding agent”

Downsides:
- not the same as a general local model server
- depends on how you want to use providers and sessions

### Option B — llama.cpp-style server
What it is:
- lightweight inference stack well suited to CPU and lower-resource setups

Advantages:
- strong fit for local CPU boxes
- efficient for quantized models
- practical on weaker machines

Downsides:
- less like a big production serving platform
- feature set depends on wrapper/server layer

### Option C — vLLM
What it is:
- high-performance model serving system with an OpenAI-compatible server

Advantages:
- excellent serving architecture
- strong batching and throughput
- great when you have stronger accelerator-backed serving needs

Downsides:
- usually most justified on GPU-heavy systems
- weaker fit for an old CPU-only or modest headless box
- may be unnecessary complexity for your current hardware mix

Why it is hard to justify here:
- your main LLM host is a 32GB CPU-only machine
- vLLM shines more in stronger accelerator environments than this specific setup

### Option D — LM Studio / llmster
What it is:
- a local model ecosystem that now has headless/server-native options

Advantages:
- easier setup for some users
- improving headless/server support via `llmster`

Downsides:
- historically more associated with desktop/local GUI usage
- for a headless Ubuntu fleet, it needs a strong reason to beat lighter or more server-native options

Why it is hard to justify here:
- your environment is headless Ubuntu
- unless llmster’s operational model is especially attractive to you, a leaner server-first stack may be cleaner

### Option E — Ollama-style runtime
What it is:
- easy local model serving with a simple interface

Advantages:
- very easy operationally
- broad community familiarity

Downsides:
- less control than lower-level stacks
- performance/serving flexibility may not be ideal for all use cases

### Practical conclusion for your environment
Best-fit proposal set:
- coding-agent layer: OpenCode
- main local model runtime: llama.cpp-style serving or equivalent lightweight CPU-friendly runtime
- optional helper/embedding runtimes: smaller dedicated services

## Recommendation

Recommended proposal: OpenCode for coding-agent workflows, llama.cpp-class serving for CPU-friendly local inference, optional smaller helper services.
