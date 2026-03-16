# Proposal — Authentication Models

## Simple explanation

This is about how the hub trusts the machines and services behind it.

In plain terms:
- who is allowed to talk to whom?

## Status

Proposal document.

## Options

### Option A — Tailscale-only trust
Meaning:
- if a machine is on your tailnet and allowed by policy, that is the trust layer

Advantages:
- simple
- fewer credentials to manage
- fits your private network design

Downsides:
- weaker application-level separation by itself
- if a machine is compromised, network trust may be too broad

Best use:
- home-lab style trusted environment with a small operator team

### Option B — Tailscale + service API keys
Meaning:
- private network plus app-level credentials between hub and services

Advantages:
- stronger than network trust alone
- clearer service identity

Downsides:
- more secrets to manage

### Option C — Mutual TLS / stronger service identity
Meaning:
- stronger cryptographic identity between internal services

Advantages:
- strongest formal separation

Downsides:
- operationally heavier
- more certificate handling

## Recommendation

Recommended proposal: Tailscale for internal transport plus app-level credentials for sensitive services.
