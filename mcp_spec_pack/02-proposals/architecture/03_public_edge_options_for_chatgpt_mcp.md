# Proposal — Public Edge Options for ChatGPT MCP

## Simple explanation

ChatGPT MCP needs a remote HTTPS endpoint. Tailscale alone is great for your private machine-to-machine traffic, but ChatGPT itself is not inside your tailnet.

In plain terms:
- your internal system can use Tailscale
- but the ChatGPT-facing MCP endpoint still needs to be reachable over HTTPS
- so you need a safe front door

## Status

Proposal document.

## Options

### Option A — Tailscale Funnel
What it is:
- a Tailscale feature that can expose a service publicly over HTTPS.

What it entails:
- keeps you in the Tailscale ecosystem
- can be simple if your tailnet policies allow it

Advantages:
- fewer extra tools
- Tailscale-managed HTTPS
- good fit if you already trust Tailscale heavily

Downsides:
- still creates a public entry point
- product limitations/policy considerations may matter
- may be less flexible than a full reverse-proxy or tunnel stack

Best use:
- you want minimal extra infrastructure

### Option B — Cloudflare Tunnel
What it is:
- a small outbound tunnel agent that gives your local hub a public HTTPS hostname.

Advantages:
- no open inbound ports
- mature public edge tooling
- can add extra access controls and policies

Downsides:
- another external service to manage
- slightly more moving parts

Best use:
- strong production-style public edge with minimal inbound exposure

### Option C — ngrok
What it is:
- hosted tunnel/public edge service for local endpoints

Advantages:
- fast to test
- easy to bring up quickly

Downsides:
- more dev/demo oriented in many setups
- long-term production fit depends on pricing and policy preference

Best use:
- prototyping and testing

### Important note
Whatever option is used, the hub origin itself should still stay private and internal where possible.

## Recommendation

For a practical long-term setup: Cloudflare Tunnel or Tailscale Funnel. For quick testing: ngrok.
