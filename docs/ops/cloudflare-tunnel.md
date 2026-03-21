# Cloudflare Tunnel Setup

This guide explains how to configure Cloudflare Tunnel to expose your GPTTalker hub over HTTPS without opening inbound ports on your network.

## Overview

Cloudflare Tunnel provides a secure way to expose web services to the internet by creating an outbound-only connection from your server to Cloudflare's edge network. This approach:

- Eliminates the need for inbound port forwarding or DMZ configuration
- Provides HTTPS encryption at Cloudflare's edge
- Protects your hub with Cloudflare's DDoS mitigation
- Keeps your home network topology private

For GPTTalker, this enables ChatGPT to connect to your hub via a public HTTPS endpoint while your hub remains protected behind your firewall.

## Prerequisites

Before setting up Cloudflare Tunnel, ensure you have:

1. **A Cloudflare account** with a registered domain
2. **Your domain's DNS managed by Cloudflare** (nameservers pointing to Cloudflare)
3. **A machine running the GPTTalker hub** that will maintain the tunnel connection
4. **Python 3.11+** with the GPTTalker hub installed

## Setup Steps

### 1. Install cloudflared

Download and install the Cloudflare Tunnel client (`cloudflared`) on the machine running your GPTTalker hub.

**Linux (amd64):**

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

**Linux (arm64):**

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
```

**macOS (Homebrew):**

```bash
brew install cloudflared
```

Verify the installation:

```bash
cloudflared --version
```

### 2. Create a Tunnel

Authenticate with Cloudflare and create a new tunnel.

```bash
cloudflared tunnel login
```

This command opens a browser window for authentication. Once authenticated, select your Cloudflare account and the domain you want to use.

Create a named tunnel:

```bash
cloudflared tunnel create gpttalker-hub
```

This command creates a tunnel and outputs a tunnel UUID. Save this UUID for the next step.

### 3. Configure the Tunnel

Create a configuration file to define how the tunnel routes traffic to your hub. The default location is `~/.cloudflared/config.yml`.

```bash
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <TUNNEL_UUID>
credentials-file: ~/.cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: gpttalker.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

Replace `<TUNNEL_UUID>` with the UUID from Step 2, and replace `gpttalker.yourdomain.com` with your desired hostname.

The configuration specifies:
- Traffic to your hostname routes to `http://localhost:8000` (your hub)
- All other traffic receives a 404 response

### 4. Configure DNS

Point your hostname to the tunnel:

```bash
cloudflared tunnel route dns gpttalker-hub gpttalker.yourdomain.com
```

This creates a CNAME record in Cloudflare pointing to your tunnel.

### 5. Get the Tunnel Token

For production use, generate a tunnel token that cloudflared uses to authenticate:

```bash
cloudflared tunnel token <TUNNEL_UUID>
```

Copy the generated token. You will need it for the hub configuration.

## Hub Configuration

Set the following environment variables on the machine running your GPTTalker hub:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GPTTALKER_CLOUDFLARE_TUNNEL_ENABLED` | Enable Cloudflare Tunnel integration | `false` | Yes (to enable) |
| `GPTTALKER_CLOUDFLARE_TUNNEL_TOKEN` | Token from Step 5 | - | Yes |
| `GPTTALKER_CLOUDFLARE_TUNNEL_HOSTNAME` | Public hostname for the hub | - | No (informational) |
| `GPTTALKER_CLOUDFLARE_TUNNEL_URL` | Local URL tunnel forwards to | `http://localhost:8000` | No |
| `GPTTALKER_CLOUDFLARE_TUNNEL_HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | `30` | No |
| `GPTTALKER_CLOUDFLARE_TUNNEL_RESTART_DELAY` | Delay before restart (seconds) | `5` | No |
| `GPTTALKER_CLOUDFLARE_TUNNEL_MAX_RESTARTS` | Max restart attempts | `5` | No |

**Example (.env file):**

```bash
GPTTALKER_CLOUDFLARE_TUNNEL_ENABLED=true
GPTTALKER_CLOUDFLARE_TUNNEL_TOKEN=eyJhciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GPTTALKER_CLOUDFLARE_TUNNEL_HOSTNAME=gpttalker.yourdomain.com
```

### Automatic Startup Behavior

When `GPTTALKER_CLOUDFLARE_TUNNEL_ENABLED=true` and `GPTTALKER_CLOUDFLARE_TUNNEL_TOKEN` is set, the hub will automatically:

1. **Start cloudflared** as a subprocess on hub startup (if not already running)
2. **Monitor tunnel health** in the background at the configured interval
3. **Auto-restart** on failure up to the configured max restarts
4. **Gracefully shutdown** the tunnel when the hub stops

### External Tunnel Detection

The hub detects if cloudflared is already managed externally:

- **Systemd service**: If `systemctl is-active cloudflared` returns "active", the hub skips subprocess management
- **Running process**: If `pgrep -x cloudflared` finds a process, the hub skips subprocess management

This allows you to run cloudflared as a systemd service while still enabling tunnel health monitoring.

### Running the Hub with Tunnel

The hub will automatically start cloudflared when the tunnel is enabled and the required environment variables are set. Ensure the hub runs as a service or in a screen/tmux session so the tunnel persists.

To test the tunnel manually:

```bash
# Test the tunnel connection
cloudflared tunnel run gpttalker-hub

# Verify HTTPS access
curl -I https://gpttalker.yourdomain.com/health
```

### Tunnel Health

You can check tunnel health via the hub's internal state:

```python
from src.hub.services.tunnel_manager import TunnelManager
from src.hub.config import get_hub_config

config = get_hub_config()
manager = TunnelManager(config)
health = await manager.health_check()
print(health)
```

The health check returns:
- `enabled`: Whether tunnel is enabled in config
- `running`: Whether tunnel is currently active
- `status`: One of: `disabled`, `external`, `healthy`, `not_running`, `crashed`
- `managed_by`: `external` if systemd/process detected
- `pid`: Process ID (if hub-managed)
- `restart_count`: Number of restarts attempted

## Security Considerations

1. **Token Security**: Treat your tunnel token as a secret. Do not commit it to version control. Use environment variables or a secrets manager.

2. **Default Deny**: The tunnel configuration uses a catch-all rule that returns 404 for unmatched traffic. This prevents unintended exposure of other services.

3. **HTTPS Only**: Cloudflare terminates TLS at the edge, providing encryption in transit. The hub communicates with cloudflared over plain HTTP on localhost.

4. **Access Control**: Consider configuring Cloudflare Access policies for additional authentication if you want to restrict who can reach your hub.

5. **Network Isolation**: The hub machine does not need any inbound ports opened. All connections originate from your machine outbound to Cloudflare.

## Troubleshooting

### Tunnel Fails to Start

- Verify the tunnel UUID is correct in your config
- Ensure the credentials file exists at `~/.cloudflared/<TUNNEL_UUID>.json`
- Check that the token has not expired

```bash
# Verify tunnel exists
cloudflared tunnel list
```

### DNS Not Resolving

- Confirm the CNAME record was created in Cloudflare DNS
- Wait up to 5 minutes for DNS propagation
- Verify your domain uses Cloudflare nameservers

```bash
# Check DNS routing
cloudflared tunnel route dns gpttalker-hub gpttalker.yourdomain.com --force
```

### Connection Refused Errors

- Ensure your hub is running and listening on the expected port (default: 8000)
- Verify the service URL in your config matches your hub's bind address
- Check that the hub binds to `127.0.0.1` or `0.0.0.0` (not disabled)

```bash
# Check if hub is listening
ss -tlnp | grep 8000
```

### Tunnel Connection Drops

- Ensure stable network connectivity from your hub machine to the internet
- Consider running cloudflared as a systemd service for automatic restarts
- Check Cloudflare status for any outages

### Certificate Errors

- Cloudflare provides certificates automatically; no manual TLS setup needed
- If using a custom certificate, verify it is valid and not expired
- Ensure the hostname matches your certificate's Common Name or Subject Alternative Name

### Tunnel Manager Issues

#### Tunnel not starting

- Verify `GPTTALKER_CLOUDFLARE_TUNNEL_ENABLED=true` is set
- Verify `GPTTALKER_CLOUDFLARE_TUNNEL_TOKEN` is set and valid
- Check hub logs for `cloudflare_tunnel_start_failed` errors
- Ensure cloudflared is installed: `cloudflared --version`

#### Too many restarts

- Check logs for `cloudflare_tunnel_max_restarts_exceeded`
- Verify network connectivity to Cloudflare
- Check if firewall is blocking outbound connections
- Consider running cloudflared as a systemd service instead

#### External vs managed conflict

- If running cloudflared manually, either stop it or let hub manage it
- If using systemd, hub will detect and skip management
- Check logs for `cloudflare_tunnel_external_detected`

## Next Steps

After completing the tunnel setup:

1. Verify the hub is accessible at your public hostname
2. Test the MCP tool endpoints
3. Configure any additional Cloudflare settings (rate limiting, WAF rules)
4. Set up monitoring for tunnel health
