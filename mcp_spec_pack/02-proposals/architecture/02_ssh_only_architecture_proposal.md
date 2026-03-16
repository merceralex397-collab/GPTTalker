# Proposal — SSH-Only Architecture

## Simple explanation

This design removes node agents.

In plain terms:
- the hub connects directly to other machines over SSH
- when it needs to inspect a repo or write a file, it runs safe predefined commands remotely
- there is less software to install, but the hub has to do more work itself

## Status

Proposal document.

## Options

### Option summary
No permanent helper service on each node. The hub uses SSH over Tailscale.

### What it can do
- inspect remote repos
- search files
- write markdown
- start approved services with restricted commands

### Advantages
- No separate agent software on each machine.
- Simpler initial rollout.
- Leverages tools Linux already has.
- Easier for a quick proof of concept.

### Downsides
- More fragile than an agent model.
- Remote command handling becomes messy.
- Harder to represent capabilities cleanly.
- Harder to maintain health/state/sessionful behavior.
- More awkward for long-lived service integrations.
- More care needed to avoid becoming “remote shell with extra steps”.

### Best use cases
- Small setups.
- Early prototypes.
- Low-maintenance environments where you do not want per-node software.

### Proposed shape
- hub on old laptop
- SSH access from hub to each machine over Tailscale
- strict command wrappers
- no arbitrary shell exposed to ChatGPT

## Recommendation

Good for a fast prototype. Weaker than node agents as a long-term architecture.
