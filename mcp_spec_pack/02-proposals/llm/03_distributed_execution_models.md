# Proposal — Distributed Execution Models

## Simple explanation

This is about how AI work is spread across machines.

In plain terms:
- do you keep one main model box, or spread work around?

## Status

Proposal document.

## Options

### Option A — Dedicated main LLM node
One stronger machine does almost all real inference.

Advantages:
- simple
- predictable
- easy to troubleshoot

Downsides:
- single bottleneck
- if that machine is busy or down, most AI work is affected

Best use:
- practical first phase

### Option C — Specialized distributed model
Different machines or services specialize.

Example:
- main machine: larger coding/reasoning model
- hub or small side machine: helper model
- embedding service: dedicated semantic indexing service

Advantages:
- better use of limited hardware
- avoids wasting heavy model time on tiny jobs
- cleaner role separation

Downsides:
- more routing complexity
- more services to monitor

Best use:
- your exact setup: old laptop hub, stronger but still limited main LLM box, mixed-purpose other machines

## Recommendation

Recommended proposal: start with A operationally, but design the specs so you can grow directly into C.
