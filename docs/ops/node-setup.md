# Node Agent Setup

This guide explains how to install, configure, and run the GPTTalker node agent on a managed machine. The node agent enables the hub to execute operations on this machine, such as repository inspection, file reading, and markdown delivery.

## Overview

The node agent is a lightweight Python service that runs on each machine you want to manage through GPTTalker. It:

- Listens for operations from the hub over Tailscale
- Executes file operations within configured boundaries
- Reports health status back to the hub
- Authenticates using API keys

## Prerequisites

Before setting up the node agent, ensure you have:

1. **Python 3.11 or later** installed on the machine
2. **Tailscale** installed and running (for hub-to-node communication)
3. **Git** to clone the repository
4. **Network access** to the hub over your Tailscale tailnet

Check your Python version:

```bash
python3 --version
```

Check Tailscale status:

```bash
tailscale status
```

## Installation Steps

### 1. Clone the Repository

Clone the GPTTalker repository to your machine:

```bash
git clone https://github.com/your-org/gpttalker.git
cd gpttalker
```

### 2. Install Dependencies

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

Alternatively, use uv for faster installation:

```bash
uv venv
source venv/bin/activate
uv pip install -e .
```

### 3. Verify Installation

Verify the node agent package is installed:

```bash
python -c "from src.node_agent import main; print('Node agent package OK')"
```

## Configuration

The node agent is configured through environment variables. Create a `.env` file in the project root or set variables in your shell.

### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `GPTTALKER_NODE_NODE_NAME` | Unique identifier for this node | `workstation-1` |
| `GPTTALKER_NODE_HUB_URL` | Hub URL (Tailscale address) | `http://100.x.x.x:8000` |
| `GPTTALKER_NODE_API_KEY` | API key for authentication | See registration guide |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GPTTALKER_NODE_OPERATION_TIMEOUT` | `60` | Operation timeout in seconds |
| `GPTTALKER_NODE_MAX_FILE_SIZE` | `10485760` | Maximum file size in bytes (10MB) |
| `GPTTALKER_NODE_ALLOWED_REPOS` | `[]` | List of allowed repository paths |
| `GPTTALKER_NODE_ALLOWED_WRITE_TARGETS` | `[]` | List of allowed write target paths |

### Example Configuration

Create a `.env` file:

```bash
# Node identity
GPTTALKER_NODE_NODE_NAME=workstation-1
GPTTALKER_NODE_HUB_URL=http://100.0.0.1:8000
GPTTALKER_NODE_API_KEY=gptk_sk_your_api_key_here

# Optional settings
GPTTALKER_NODE_OPERATION_TIMEOUT=120
GPTTALKER_NODE_MAX_FILE_SIZE=20971520

# Security boundaries (absolute paths)
GPTTALKER_NODE_ALLOWED_REPOS=/home/user/repos,/projects
GPTTALKER_NODE_ALLOWED_WRITE_TARGETS=/home/user/repos/docs
```

### Path Validation Rules

- All paths in `ALLOWED_REPOS` and `ALLOWED_WRITE_TARGETS` must be **absolute paths**
- Node name must match pattern: `^[a-zA-Z0-9_-]+$`
- Hub URL must start with `http://` or `https://`

## Starting the Node Agent

### Development Mode

Run the node agent directly for development:

```bash
cd gpttalker
source venv/bin/activate
python -m src.node_agent.main
```

The node agent will start and attempt to connect to the hub.

### Production Mode

For production deployment, run as a systemd service:

**1. Create a service file** (`/etc/systemd/system/gpttalker-node.service`):

```ini
[Unit]
Description=GPTTalker Node Agent
After=network.target tailscaled.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/gpttalker
Environment="PATH=/home/youruser/gpttalker/venv/bin"
EnvironmentFile=/home/youruser/gpttalker/.env
ExecStart=/home/youruser/gpttalker/venv/bin/python -m src.node_agent.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**2. Enable and start the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable gpttalker-node
sudo systemctl start gpttalker-node
```

**3. Check status:**

```bash
sudo systemctl status gpttalker-node
```

## Verifying the Node is Running

### Check Local Health

The node agent exposes a health endpoint:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{
  "status": "healthy",
  "node_name": "workstation-1",
  "version": "0.1.0"
}
```

### Check Hub Registration

From the hub machine (or any machine with MCP tools), verify the node appears:

```bash
# Using the hub's list_nodes tool
python -m src.hub.main --tool list_nodes
```

The registered node should appear with health status.

### Check Tailscale Connectivity

Verify the node is reachable over Tailscale:

```bash
# From hub machine
ping -c 3 <node-tailcale-hostname>
```

## Troubleshooting

### Node Fails to Start

**Error: "node_name cannot be empty"**

- Ensure `GPTTALKER_NODE_NODE_NAME` is set in your environment
- Node name must match pattern: `^[a-zA-Z0-9_-]+$`

**Error: "hub_url cannot be empty"**

- Ensure `GPTTALKER_NODE_HUB_URL` is set
- URL must start with `http://` or `https://`

**Error: "Path must be absolute"**

- Check `GPTTALKER_NODE_ALLOWED_REPOS` and `GPTTALKER_NODE_ALLOWED_WRITE_TARGETS`
- All paths must be absolute (e.g., `/home/user/repos`, not `~/repos`)

### Cannot Connect to Hub

**Symptom: Connection refused errors**

1. Verify the hub is running:
   ```bash
   curl http://<hub-ip>:8000/health
   ```

2. Verify Tailscale connectivity:
   ```bash
   tailscale status
   ping -c 3 <hub-tailcale-ip>
   ```

3. Check the hub URL in your configuration matches the hub's Tailscale IP

**Symptom: Authentication errors**

- Verify the API key matches the key registered with the hub
- See the [Node Registration Guide](node-registration.md) for key setup

### Permission Denied Errors

**Symptom: "Path not in allowed list"**

- The node agent rejects operations outside configured boundaries
- Add the required paths to `GPTTALKER_NODE_ALLOWED_REPOS` or `GPTTALKER_NODE_ALLOWED_WRITE_TARGETS`
- Restart the node agent after updating configuration

### Operation Timeouts

**Symptom: Operations fail with timeout**

1. Increase `GPTTALKER_NODE_OPERATION_TIMEOUT` for slow operations
2. Check network latency between node and hub
3. Verify no firewall is blocking Tailscale traffic

### Logs

Check logs for detailed error information:

```bash
# Systemd
journalctl -u gpttalker-node -f

# Development mode
python -m src.node_agent.main
```

## Security Considerations

1. **API Key Security**: Treat your API key as a secret. Do not commit it to version control. Use environment variables or a secrets manager.

2. **Path Boundaries**: The node agent only allows operations within `ALLOWED_REPOS` and `ALLOWED_WRITE_TARGETS`. Configure these carefully.

3. **Network Isolation**: The node agent communicates only over Tailscale. Ensure your tailnet is properly secured.

4. **Default Deny**: Unknown paths, repos, and operations are rejected. Fail-closed behavior is enforced.

## Next Steps

After setting up the node agent:

1. Complete [Node Registration](node-registration.md) to register with the hub
2. Verify the node appears in `list_nodes` output
3. Test a simple operation like `inspect_repo_tree`

## Reference

- [Node Registration Guide](node-registration.md)
- [Hub Configuration](../hub/config.md)
- [ngrok Setup](ngrok.md)
