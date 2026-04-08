# Node Registration Guide

This guide explains how to register a node agent with the GPTTalker hub, enabling the hub to discover and route operations to that machine.

## Overview

Node registration establishes a trust relationship between the hub and a node agent. During registration:

1. The operator generates an API key for the node
2. The node is added to the hub's node registry
3. The node agent receives credentials to authenticate with the hub
4. The hub begins polling the node for health status

## Registration Flow

The registration process involves these steps:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Generate    │     │  2. Register    │     │  3. Connect    │
│  API Key        │────▶│  Node           │────▶│  & Verify       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Prerequisites

Before registering a node, ensure:

1. The **hub is running** and accessible over Tailscale
2. The **node agent is installed** on the target machine
3. You have **operator access** to the hub (to run management tools)
4. You know the **node's Tailscale IP** or hostname

## Step 1: Generate an API Key

API keys authenticate the node agent when connecting to the hub. Generate a secure API key:

```bash
# Generate a secure random key
python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
```

This outputs a key like: `gptk_sk_aB3cD4eF5gH6iJ7kL8mN9oP0qR`

Store this key securely. You will need it for:
- The node agent configuration
- Node registration with the hub

## Step 2: Register the Node

Register the node with the hub using the hub's management interface. You can do this through:

### Option A: Using the Hub CLI

If you have direct access to the hub machine:

```bash
# Activate the hub's virtual environment
source venv/bin/activate

# Register the node (requires hub admin access)
python -c "
import asyncio
from src.hub.services.node_repository import NodeRepository
from src.shared.database import get_db_connection

async def register_node():
    async with get_db_connection() as db:
        repo = NodeRepository(db)
        await repo.create(
            name='workstation-1',
            tailscale_hostname='workstation-1.tail-scale.ts.net',
            api_key='gptk_sk_your_key_here',
            description='Primary workstation'
        )
        print('Node registered successfully')

asyncio.run(register_node())
"
```

### Option B: Using the MCP Tool (via ChatGPT)

If you have MCP tools exposed, you can register through the hub's MCP interface. Use the `register_node` tool if available, or manually insert via SQLite:

```bash
# Connect to the hub's database
sqlite3 /path/to/gpttalker/data/gpttalker.db

# Insert node record
INSERT INTO nodes (id, name, tailscale_hostname, api_key, description, status, created_at, updated_at)
VALUES (
    'node_' || lower(hex(randomblob(4))),
    'workstation-1',
    'workstation-1.tail-scale.ts.net',
    'gptk_sk_your_key_here',
    'Primary workstation',
    'pending',
    datetime('now'),
    datetime('now')
);
```

### Node Registration Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `name` | Unique node identifier | Yes |
| `tailscale_hostname` | Tailscale DNS name | Yes |
| `api_key` | Authentication key | Yes |
| `description` | Human-readable description | No |
| `status` | Initial status (`pending` or `active`) | No (default: `pending`) |

## Step 3: Configure the Node Agent

On the node machine, configure the agent with the registration details:

```bash
# Create or edit .env file
cat > /home/user/gpttalker/.env << 'EOF'
# Node identity (must match registration)
GPTTALKER_NODE_NODE_NAME=workstation-1

# Hub connection (use Tailscale address)
GPTTALKER_NODE_HUB_URL=http://100.0.0.1:8000

# Authentication (from Step 1)
GPTTALKER_NODE_API_KEY=gptk_sk_your_key_here

# Optional: Configure allowed paths
GPTTALKER_NODE_ALLOWED_REPOS=/home/user/repos
GPTTALKER_NODE_ALLOWED_WRITE_TARGETS=/home/user/repos/docs
EOF
```

Replace:
- `workstation-1` with your registered node name
- `100.0.0.1` with your hub's Tailscale IP
- `gptk_sk_your_key_here` with your API key

## Step 4: Start the Node Agent

Start the node agent on the target machine:

```bash
# Development mode
cd /home/user/gpttalker
source venv/bin/activate
python -m src.node_agent.main
```

Or, if using systemd:

```bash
sudo systemctl start gpttalker-node
```

## Step 5: Verify Registration

### Check Node Status

From any machine with hub access, verify the node is registered and healthy:

```bash
# Using the hub's list_nodes tool
python -c "
import asyncio
from src.hub.services.node_repository import NodeRepository
from src.shared.database import get_db_connection

async def list_nodes():
    async with get_db_connection() as db:
        repo = NodeRepository(db)
        nodes = await repo.list_all()
        for node in nodes:
            print(f\"{node['name']}: {node['status']} (last_seen: {node.get('last_seen')})\")
        return nodes

asyncio.run(list_nodes())
"
```

Expected output:

```
workstation-1: healthy (last_seen: 2026-03-17 10:30:00)
```

### Test Node Connectivity

Verify the hub can communicate with the node:

```bash
# Ping the node's health endpoint via Tailscale
curl http://workstation-1.tail-scale.ts.net:8001/health
```

Expected response:

```json
{
  "status": "healthy",
  "node_name": "workstation-1",
  "version": "0.1.0"
}
```

### Test an Operation

Try a simple operation to ensure the node responds to hub requests:

```bash
# List allowed repos (if configured)
python -c "
import asyncio
from src.hub.services.hub_node_client import HubNodeClient
from src.shared.context import trace_id_var

async def test_operation():
    async with HubNodeClient('http://100.0.0.1:8000', 'gptk_sk_your_key') as client:
        result = await client.list_allowed_paths('workstation-1')
        print(result)

asyncio.run(test_operation())
"
```

## Deregistration Process

To remove a node from the hub:

### Step 1: Stop the Node Agent

On the node machine:

```bash
# Development mode: Ctrl+C
# Systemd:
sudo systemctl stop gpttalker-node
sudo systemctl disable gpttalker-node
```

### Step 2: Remove from Hub Registry

**Option A: Using the Hub CLI**

```bash
python -c "
import asyncio
from src.hub.services.node_repository import NodeRepository
from src.shared.database import get_db_connection

async def deregister_node():
    async with get_db_connection() as db:
        repo = NodeRepository(db)
        await repo.delete('workstation-1')
        print('Node deregistered successfully')

asyncio.run(deregister_node())
"
```

**Option B: Using SQLite**

```bash
sqlite3 /path/to/gpttalker/data/gpttalker.db
DELETE FROM nodes WHERE name = 'workstation-1';
```

### Step 3: Revoke API Key

If the API key was stored in a secrets manager, revoke or rotate it:

```bash
# Generate a new key
python -c "from secrets import token_urlsafe; print(token_urlsafe(32))"
```

### Step 4: Verify Removal

Confirm the node no longer appears:

```bash
python -c "
import asyncio
from src.hub.services.node_repository import NodeRepository
from src.shared.database import get_db_connection

async def verify_removal():
    async with get_db_connection() as db:
        repo = NodeRepository(db)
        nodes = await repo.list_all()
        print(f'Remaining nodes: {len(nodes)}')

asyncio.run(verify_removal())
"
```

## API Key Management

### Rotating API Keys

To rotate an API key without downtime:

1. **Generate a new key** (Step 1 in registration)
2. **Update the node's configuration** with the new key
3. **Restart the node agent** to pick up the new key
4. **Verify the node connects** with the new key
5. **Remove the old key** from the hub registry

```bash
# On node: Update .env with new key
GPTTALKER_NODE_API_KEY=gptk_sk_new_key_here

# Restart node
sudo systemctl restart gpttalker-node
```

### Multiple Nodes

Each node should have its own unique API key. Do not share keys across nodes. This:

- Enables per-node access revocation
- Provides audit trail for operations
- Isolates security boundaries

## Troubleshooting

### Node Not Appearing in list_nodes

**Possible causes:**

1. Node agent not running - start the agent
2. Wrong node name - verify the name matches registration
3. Hub unreachable - check Tailscale connectivity

**Resolution:**

```bash
# Check node agent is running locally
curl http://localhost:8001/health

# Check Tailscale connectivity from hub
ping -c 3 workstation-1.tail-scale.ts.net
```

### Authentication Failures

**Error: "401 Unauthorized" or "Invalid API key"**

- Verify the API key matches exactly (no extra spaces)
- Check the key is registered in the hub's database
- Ensure `GPTTALKER_NODE_API_KEY` is set correctly

```bash
# Verify key in node config
grep API_KEY /home/user/gpttalker/.env
```

### Health Check Failing

**Error: Node shows as "unhealthy" or "offline"**

1. Check the node agent logs for errors
2. Verify the node can reach the hub over Tailscale
3. Ensure the node's hostname matches the registration

```bash
# Check node logs
journalctl -u gpttalker-node -n 50

# Test connectivity
curl http://<hub-tailscale-ip>:8000/health
```

### Registration Permission Denied

**Error: "Permission denied" when registering**

- Ensure you have write access to the hub's SQLite database
- If using the CLI tool, verify you have hub operator permissions

## Security Considerations

1. **Key Storage**: Store API keys securely. Use environment variables, not hardcoded values.

2. **Key Rotation**: Rotate API keys periodically, especially if a node is decommissioned.

3. **Unique Keys**: Each node should have a unique API key. Never share keys.

4. **Network Trust**: Nodes authenticate over Tailscale. Ensure your tailnet is trusted.

5. **Access Logging**: All node operations are logged with trace IDs for audit purposes.

## Reference

- [Node Agent Setup](node-setup.md)
- [Hub Configuration](../hub/config.md)
- [ngrok Setup](ngrok.md)
