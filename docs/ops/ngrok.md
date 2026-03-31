# ngrok Setup

This guide explains how to configure ngrok to expose your GPTTalker hub over HTTPS without opening inbound ports on your network.

## Overview

ngrok provides a secure public HTTPS edge for GPTTalker while the hub continues to listen only on the local machine. In GPTTalker, ngrok is the only canonical public-edge provider after the March 31, 2026 architecture pivot.

This approach:

- avoids inbound port forwarding
- gives the hub a public HTTPS endpoint for ChatGPT MCP connectivity
- keeps internal hub-to-node traffic on Tailscale
- lets the hub manage ngrok directly or detect when ngrok is already managed externally

## Prerequisites

Before setting up ngrok, ensure you have:

1. An ngrok account and authtoken
2. A machine running the GPTTalker hub
3. Python 3.11+ with the GPTTalker hub installed
4. `ngrok` installed on the hub machine

## Setup Steps

### 1. Install ngrok

Install the ngrok agent on the machine running the GPTTalker hub.

```bash
brew install ngrok/ngrok/ngrok
ngrok version
```

Or install it with your preferred Linux package method from the official ngrok distribution instructions.

### 2. Choose your forwarding mode

GPTTalker supports two practical modes:

- Random ngrok URL assigned at process start
- Reserved/custom ngrok URL supplied through configuration

The hub forwards traffic to `http://localhost:8000` by default.

### 3. Configure the hub environment

Set the following environment variables on the machine running your GPTTalker hub:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GPTTALKER_NGROK_ENABLED` | Enable ngrok subprocess management | `false` | Yes (to enable) |
| `GPTTALKER_NGROK_AUTHTOKEN` | ngrok authtoken used when the hub manages the process | - | Yes, unless ngrok is already managed externally |
| `GPTTALKER_NGROK_PUBLIC_URL` | Optional fixed ngrok URL, for example `https://gpttalker.ngrok.app` | - | No |
| `GPTTALKER_NGROK_FORWARD_URL` | Local hub URL ngrok forwards to | `http://localhost:8000` | No |
| `GPTTALKER_NGROK_HEALTH_CHECK_INTERVAL` | Health check interval in seconds | `30` | No |
| `GPTTALKER_NGROK_RESTART_DELAY` | Delay before restart in seconds | `5` | No |
| `GPTTALKER_NGROK_MAX_RESTARTS` | Maximum restart attempts before giving up | `5` | No |

Example:

```bash
GPTTALKER_NGROK_ENABLED=true
GPTTALKER_NGROK_AUTHTOKEN=2abc123example
GPTTALKER_NGROK_PUBLIC_URL=https://gpttalker.ngrok.app
GPTTALKER_NGROK_FORWARD_URL=http://localhost:8000
```

### 4. Start the hub

When `GPTTALKER_NGROK_ENABLED=true`, GPTTalker will:

1. detect whether `ngrok` is already managed externally
2. start `ngrok http` itself when hub-managed mode is required
3. monitor the subprocess and restart it on failure up to the configured limit
4. stop the hub-managed subprocess during shutdown

Internally, the hub launches ngrok with the equivalent of:

```bash
ngrok http http://localhost:8000 --authtoken "$GPTTALKER_NGROK_AUTHTOKEN" --url "$GPTTALKER_NGROK_PUBLIC_URL"
```

The `--url` flag is omitted when `GPTTALKER_NGROK_PUBLIC_URL` is not set, so ngrok assigns a random public hostname.

### 5. Verify the public edge

```bash
curl -I https://your-ngrok-endpoint/health
```

## External ngrok Detection

The hub detects external ngrok management in two ways:

- `pgrep -x ngrok`
- `systemctl is-active ngrok`

If either indicates ngrok is already running, GPTTalker leaves the external process alone and reports the tunnel as externally managed.

## Tunnel Health

You can inspect the current tunnel state through the runtime manager:

```python
from src.hub.config import get_hub_config
from src.hub.services.tunnel_manager import TunnelManager

config = get_hub_config()
manager = TunnelManager(config)
health = await manager.health_check()
print(health)
```

The health payload includes:

- `enabled`
- `running`
- `status`
- `managed_by` when external management is detected
- `pid` when the hub owns the ngrok subprocess
- `restart_count`
- `provider`

## Security Considerations

1. Treat the ngrok authtoken as a secret.
2. Keep GPTTalker itself fail-closed; ngrok only exposes the hub endpoint, not arbitrary system services.
3. Keep hub-to-node traffic on Tailscale even though the public edge is internet-facing.
4. If you use a stable ngrok URL, secure it with ngrok traffic policy or another access-control layer when appropriate.

## Troubleshooting

### ngrok does not start

- Verify `GPTTALKER_NGROK_ENABLED=true`
- Verify `GPTTALKER_NGROK_AUTHTOKEN` is set when the hub is expected to manage ngrok
- Ensure `ngrok` is installed and on `PATH`

### Public URL is not the one you expect

- Check `GPTTALKER_NGROK_PUBLIC_URL`
- If you need a fixed hostname, confirm it is provisioned in your ngrok account before using it

### Requests do not reach the hub

- Confirm the hub is listening on the address in `GPTTALKER_NGROK_FORWARD_URL`
- Confirm the local service is reachable on `localhost:8000` or your chosen upstream URL

## Reference

- [Node Agent Setup](node-setup.md)
- [Node Registration Guide](node-registration.md)
- [Hub Configuration](../hub/config.md)
