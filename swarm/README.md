# AI Swarm - Distributed Agent Execution

A secure, multi-device AI agent swarm connecting CoPaw (WSL) to remote agents (macOS) via Redis queue and Tailscale VPN.

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   CoPaw     │ ───────>│    Redis    │ <───────│   Worker    │
│   (WSL)     │ enqueue │   Queue     │ dequeue │  (Docker)   │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                       │
                              Tailscale VPN            │ HMAC-signed
                                                       │ HTTP Request
                                                       ▼
                                               ┌─────────────┐
                                               │    Bridge   │
                                               │    API      │
                                               │   (macOS)   │
                                               └──────┬──────┘
                                                      │
                                               ┌──────▼──────┐
                                               │ Capabilities│
                                               │  Executor   │
                                               └─────────────┘
```

## Components

- **Worker** (`swarm/worker/`): Polls Redis for jobs, routes to Bridge API with HMAC authentication
- **Bridge** (`swarm/bridge/`): FastAPI server on macOS that executes capabilities
- **Client** (`swarm/client/`): Python library for enqueuing jobs
- **CLI** (`copaw swarm`): Command-line interface for swarm management

## Quick Start

### Prerequisites

1. Tailscale account with auth key
2. Both devices (WSL + Mac) on same Tailscale network
3. Docker and Docker Compose on WSL
4. Python 3.11+ on both systems

### 1. Configure Environment

On WSL (CoPaw):
```bash
cp .env.swarm.example .env.swarm
# Edit .env.swarm and set:
# - BRIDGE_HOST: Tailscale IP of your Mac
# - HMAC_SECRET: Shared secret (min 32 chars)
```

On Mac (Accomplish):
```bash
cd swarm/bridge
cp .env.bridge.example .env.bridge
# Edit .env.bridge and set:
# - HMAC_SECRET: Same secret as WSL
# - ALLOWED_IPS: Tailscale IP of WSL
```

### 2. Start Infrastructure

On WSL:
```bash
# Start Redis and Worker
docker compose -f docker-compose.swarm.yml up -d

# Check status
docker compose -f docker-compose.swarm.yml logs -f
```

On Mac:
```bash
cd swarm/bridge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 3. Use the CLI

```bash
# Check swarm status
copaw swarm status

# List available capabilities
copaw swarm capabilities

# Enqueue a job
copaw swarm enqueue browser:open -p url=https://example.com

# Execute and wait for result
copaw swarm enqueue file:read -p path=~/Documents/file.txt --wait

# Get result of a job
copaw swarm result <job-id>
```

## Security

- **HMAC-SHA256**: All requests signed with shared secret
- **IP Allowlist**: Bridge only accepts connections from specific Tailscale IPs
- **Path Traversal Protection**: File operations restricted to home directory
- **Command Blocking**: Dangerous shell commands are blocked
- **Non-root Containers**: Docker containers run as unprivileged user

## Capabilities

| Capability | Description | Parameters |
|------------|-------------|------------|
| `browser:open` | Open URL in default browser | `url` |
| `browser:screenshot` | Take webpage screenshot | `url` |
| `shell:execute` | Execute shell command | `command` |
| `file:read` | Read file contents | `path` |
| `file:write` | Write to file | `path`, `content` |
| `file:list` | List directory | `path` |

## Testing

```bash
# Run all swarm tests
python -m pytest tests/swarm/ -v

# Run security validation
./scripts/validate-security.sh
```

## Development

### Project Structure

```
swarm/
├── worker/           # Job worker (runs on WSL)
│   ├── main.py      # Worker service
│   ├── config.py    # Configuration
│   ├── Dockerfile   # Container image
│   └── requirements.txt
├── bridge/          # Bridge API (runs on Mac)
│   ├── main.py      # FastAPI server
│   ├── config.py    # Settings
│   ├── capabilities.py  # Capability handlers
│   ├── Dockerfile   # Container image
│   ├── docker-compose.bridge.yml
│   └── requirements.txt
├── client/          # Python client library
│   ├── client.py    # JobQueue class
│   └── config.py    # Client config
└── README.md        # This file
```

### Adding New Capabilities

1. Add capability definition to `swarm/bridge/capabilities.py`
2. Implement handler method `_handle_<capability_name>`
3. Add tests in `tests/swarm/test_bridge_api.py`
4. Update capability list in `src/copaw/cli/swarm_cmd.py`

## Troubleshooting

### Worker can't connect to Redis
- Ensure Redis container is running: `docker ps`
- Check Redis logs: `docker logs swarm_redis`

### HMAC signature mismatch
- Verify `HMAC_SECRET` is identical on both sides
- Check that system time is synchronized

### Bridge rejects requests
- Verify `ALLOWED_IPS` includes WSL's Tailscale IP
- Check Tailscale is connected on both devices: `tailscale status`

## License

Same as CoPaw project.
