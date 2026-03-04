# AI Swarm Documentation

Secure, multi-device AI agent swarm connecting CoPaw (WSL) to Accomplish (macOS) via Redis queue and Tailscale VPN.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Swarm Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐        ┌──────────────┐       ┌─────────────┐ │
│  │   CoPaw     │        │    Redis      │       │   Bridge    │ │
│  │   (WSL)     │───────▶│   Queue      │◀──────│   (Mac)     │ │
│  │             │        │              │       │             │ │
│  │ ┌─────────┐ │        │ ┌──────────┐ │       │ ┌─────────┐ │ │
│  │ │ Client  │ │        │ │ Pending  │ │       │ │ Worker  │ │ │
│  │ │         │ │        │ │ Jobs     │ │       │ │         │ │ │
│  │ │ Enqueue │ │        │ └──────────┘ │       │ │ Execute │ │ │ │
│  │ │ Jobs    │ │        └──────────────┘       │ │ Jobs    │ │ │ │
│  │ └─────────┘ │                             │ └─────────┘ │ │ │
│  │      │       │                             │      │       │ │ │
│  │ ┌─────────┐ │                             │ ┌─────────┐ │ │ │
│  │ │  CLI    │ │                             │ │Audit Log│ │ │ │
│  │ │Commands │ │                             │ └─────────┘ │ │ │
│  │ └─────────┘ │                             └─────────────┘ │ │
│  └─────────────┘                                             │ │
│         │                                                    │ │
│  Tailscale VPN ────────────────────────────────────────────│ │
│  (Encrypted)                                               └─┘
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Redis Queue
- Central job queue for distributing work
- Results stored with 24-hour TTL
- Healthchecks configured

### 2. Job Worker (WSL)
- Polls Redis for pending jobs
- Signs requests with HMAC-SHA256
- Routes jobs to Bridge API

### 3. Bridge API (Mac)
- FastAPI server with HMAC authentication
- IP allowlist for Tailscale network
- Capability executor with audit logging

### 4. Job Queue Client
- Python library for enqueuing jobs
- Synchronous and asynchronous modes
- CLI integration via `copaw swarm`

## Security Features

| Feature | Implementation |
|---------|---------------|
| Authentication | HMAC-SHA256 signatures |
| Network | Tailscale VPN (WireGuard) |
| IP Filtering | Allowlist for worker IPs |
| Path Security | Home directory restriction |
| Shell Security | Dangerous command blocking |
| Container | Non-root user execution |

## Quick Start

### Prerequisites

1. Tailscale account with auth key
2. Both devices on same Tailscale network
3. Docker and Docker Compose on WSL
4. Python 3.11+ on both systems

### 1. Setup WSL (CoPaw)

```bash
# 1. Copy environment template
cp .env.swarm.example .env.swarm

# 2. Edit configuration
vim .env.swarm
```

```env
# .env.swarm
BRIDGE_HOST=100.x.x.x  # Your Mac's Tailscale IP
HMAC_SECRET=your-secret-min-32-chars-long
POLL_INTERVAL=5
```

```bash
# 3. Start infrastructure
docker compose -f docker-compose.swarm.yml up -d

# 4. Verify
 docker ps
```

### 2. Setup Mac (Accomplish)

```bash
# 1. Copy environment template
cd swarm/bridge
cp .env.bridge.example .env.bridge

# 2. Edit configuration
vim .env.bridge
```

```env
# .env.bridge
HMAC_SECRET=your-secret-min-32-chars-long
ALLOWED_IPS=100.x.x.x,100.y.y.y  # CoPaw's Tailscale IP
```

```bash
# 3. Start bridge
docker compose -f docker-compose.bridge.yml up -d

# 4. Verify
 curl http://localhost:8765/health
```

### 3. Test Connection

```bash
# Using CLI
copaw swarm status
copaw swarm capabilities

# Enqueue a job
copaw swarm enqueue browser:open -p url=https://example.com -w

# Check result
copaw swarm result <job-id>
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `copaw swarm status` | Check swarm status |
| `copaw swarm up` | Start infrastructure |
| `copaw swarm down` | Stop infrastructure |
| `copaw swarm logs` | View logs |
| `copaw swarm enqueue <capability>` | Queue a job |
| `copaw swarm result <job-id>` | Get job result |
| `copaw swarm capabilities` | List capabilities |
| `copaw swarm config` | Show configuration |

## Capabilities

| Capability | Parameters | Description |
|------------|-----------|-------------|
| `browser:open` | `url` | Open URL in default browser |
| `browser:screenshot` | `url` | Take webpage screenshot |
| `shell:execute` | `command` | Execute shell command |
| `file:read` | `path` | Read file contents |
| `file:write` | `path`, `content` | Write to file |
| `file:list` | `path` | List directory contents |

## Python API

```python
from swarm.client.client import JobQueue

# Connect to Redis
queue = JobQueue()
queue.connect()

# Enqueue job
job_id = queue.enqueue(
    capability="browser:open",
    parameters={"url": "https://example.com"}
)

# Wait for result
result = queue.get_result(job_id, timeout=60)
print(result)

# Or execute synchronously
result = queue.execute(
    capability="file:read",
    parameters={"path": "~/Documents/file.txt"},
    timeout=30
)
```

## Security Validation

Run before deployment:

```bash
./scripts/validate-security.sh
```

## Troubleshooting

### Redis Connection Failed

```bash
# Check Redis is running
docker ps | grep redis

# Check Redis logs
docker logs swarm_redis
```

### HMAC Verification Failed

- Ensure `HMAC_SECRET` matches on both sides
- Secret must be at least 32 characters

### Bridge Not Responding

- Check Mac is on Tailscale
- Verify `ALLOWED_IPS` includes CoPaw's Tailscale IP
- Check Bridge logs: `docker logs swarm_bridge`

## File Structure

```
swarm/
├── bridge/              # Mac-side Bridge API
│   ├── main.py         # FastAPI server
│   ├── config.py       # Configuration
│   ├── capabilities.py # Capability handlers
│   ├── Dockerfile
│   ├── docker-compose.bridge.yml
│   └── .env.bridge.example
├── client/             # WSL-side client library
│   ├── client.py       # JobQueue class
│   ├── config.py       # Configuration
│   └── requirements.txt
└── worker/             # Job worker service
    ├── main.py         # Worker main loop
    ├── config.py       # Configuration
    ├── Dockerfile
    └── requirements.txt

tests/swarm/            # Integration tests
├── test_hmac.py
├── test_job_queue.py
└── test_bridge_api.py

scripts/
└── validate-security.sh  # Security validation

docker-compose.swarm.yml  # WSL infrastructure
.env.swarm.example       # Environment template
```

## Development

### Run Tests

```bash
python -m pytest tests/swarm/ -v
```

### Build Images

```bash
# Worker
docker build -t swarm-worker:latest swarm/worker/

# Bridge
cd swarm/bridge && docker build -t swarm-bridge:latest .
```

## License

Same as CoPaw project.
