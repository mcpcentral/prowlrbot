# Deployment Guide

How to run ProwlrBot in production: Docker, fly.io, or a plain Linux server.

---

## Run locally vs use our hosted app

| | **Run locally** | **Use our hosted app** |
|--|------------------|-------------------------|
| **What** | You run `prowlr app` on your machine (or your server). | One shared instance we host (e.g. app.prowlrbot.com). |
| **Workspace** | One: your machine’s working dir (e.g. `~/.prowlrbot`). | One: the server’s working dir; all app users share it. |
| **Who can sign up** | Only people with access to that machine (or you create users). | Anyone can register on the app and get an account. |
| **Credits** | Stored locally (e.g. `~/.prowlrbot/marketplace.db`). Set `PROWLR_FREE_TIER_WELCOME_CREDITS` to grant welcome credits to new users. | Same logic on the server; Stripe for paid tiers if configured. |

For details on sign-up, credits, and workspace (who gets what), see [Sign-up, credits, and workspace](signup-credits-and-workspace.md).

---

## Quick start (development / local)

```bash
pip install prowlrbot
prowlr init --defaults
prowlr env set OPENAI_API_KEY sk-...
prowlr app
```

Open `http://localhost:8088`.

---

## Docker

### Full image (with browser automation)

Includes Chromium + Xvfb for the `browser_visible` and `screenshot` tools.

```bash
git clone https://github.com/ProwlrBot/prowlrbot.git
cd prowlrbot

# Build
docker build -f deploy/Dockerfile -t prowlrbot:latest .

# Run
docker run -d \
  --name prowlrbot \
  -p 8088:8088 \
  -e OPENAI_API_KEY=sk-... \
  -v prowlrbot-data:/app/working \
  prowlrbot:latest
```

The image:
- Stage 1 builds the React console (`npm run build`)
- Stage 2: node:20-slim base with Chromium, Xvfb, XFCE4, supervisord
- Runs `prowlr init --defaults --accept-security` at build time
- Default port: 8088 (override with `-e PROWLRBOT_PORT=3000`)

Channels enabled by default: `dingtalk`, `feishu`, `qq`, `console`. Discord and iMessage are excluded from this image. Override with:

```bash
-e PROWLRBOT_ENABLED_CHANNELS=discord,telegram,console
```

### Environment variables for Docker

```bash
docker run -d \
  --name prowlrbot \
  -p 8088:8088 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e PROWLRBOT_PORT=8088 \
  -e PROWLRBOT_WORKING_DIR=/app/working \
  -v prowlrbot-data:/app/working \
  prowlrbot:latest
```

### Lean image (headless only)

`deploy/Dockerfile.fly` is a stripped-down image with no desktop environment — suitable for fly.io and any cloud that doesn't need GUI browser tools:

```bash
docker build -f deploy/Dockerfile.fly -t prowlrbot:fly .

docker run -d \
  -p 8088:8088 \
  -e OPENAI_API_KEY=sk-... \
  -e PROWLRBOT_RUNNING_IN_CONTAINER=1 \
  -v prowlrbot-data:/data \
  prowlrbot:fly
```

Differences from full image:
- python:3.12-slim base (~150 MB vs ~1.5 GB)
- No Xvfb/XFCE4 (no visible browser tool)
- Chromium still included for headless browser use
- `PROWLRBOT_RUNNING_IN_CONTAINER=1` disables browser_visible at runtime
- Working dir: `/data` (mount a volume here)

---

## Docker Compose (bridge + workers)

For the war room hub setup with multiple worker containers:

```bash
cd docker
cp .env.example .env   # edit HUB_SECRET, etc.
docker compose up -d

# Scale to 4 workers
docker compose up -d --scale worker=4
```

`docker/docker-compose.yml` runs:
- `bridge`: ProwlrHub HTTP/SQLite bridge on port 8099
- `worker`: worker containers that connect to the bridge

---

## Fly.io

Fly.io is the recommended cloud platform for ProwlrBot. The lean Dockerfile is optimized for it.

### Prerequisites

```bash
brew install flyctl
fly auth login
```

### Deploy

```bash
cd prowlrbot
fly launch --dockerfile deploy/Dockerfile.fly --name my-prowlrbot

# Set secrets
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set ANTHROPIC_API_KEY=sk-ant-...

# Create persistent volume for data
fly volumes create prowlrbot_data --region iad --size 3

# Mount the volume (edit fly.toml)
```

In `fly.toml`:

```toml
[build]
  dockerfile = "deploy/Dockerfile.fly"

[[mounts]]
  source = "prowlrbot_data"
  destination = "/data"

[[services]]
  protocol = "tcp"
  internal_port = 8088

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

Then deploy:

```bash
fly deploy
```

### Scale up if you need browser tools

The lean fly image includes headless Chromium. For full `browser_visible` support, use the full Dockerfile and a larger VM:

```bash
fly scale vm shared-cpu-4x
# or
fly scale vm dedicated-cpu-1x
```

---

## Linux server (systemd)

For a persistent deployment on a VPS or bare-metal server:

### Install

```bash
# As a non-root user
python3 -m venv /opt/prowlrbot
source /opt/prowlrbot/bin/activate
pip install prowlrbot

prowlr env set OPENAI_API_KEY sk-...
prowlr init --defaults
```

### Create systemd service

```ini
# /etc/systemd/system/prowlrbot.service
[Unit]
Description=ProwlrBot
After=network.target

[Service]
Type=simple
User=prowlr
Group=prowlr
WorkingDirectory=/opt/prowlrbot
ExecStart=/opt/prowlrbot/bin/prowlr app --host 0.0.0.0 --port 8088
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable prowlrbot
sudo systemctl start prowlrbot
sudo systemctl status prowlrbot
sudo journalctl -u prowlrbot -f   # follow logs
```

### Reverse proxy (nginx)

```nginx
server {
    listen 80;
    server_name prowlrbot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo certbot --nginx -d prowlrbot.example.com
```

---

## Environment variables reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PROWLRBOT_WORKING_DIR` | `~/.prowlrbot` | Data directory |
| `PROWLRBOT_SECRET_DIR` | `~/.prowlrbot.secret` | Secrets directory |
| `PROWLRBOT_PORT` | `8088` | Server port |
| `PROWLRBOT_RUNNING_IN_CONTAINER` | unset | Set to `1` to disable browser_visible |
| `PROWLRBOT_ENABLED_CHANNELS` | all | Comma-separated channel list |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` | auto | Custom Chromium path |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | unset | Set to `1` to skip auto-download |

---

## Health check

```bash
curl http://localhost:8088/api/version
# {"version":"...", "status":"ok"}

curl http://localhost:8088/api/agents
# [{"id": "...", "name": "...", ...}]
```

For Docker:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8088/api/version || exit 1
```

---

## Data persistence

All data lives in two directories:

| Path | Contains | Back up? |
|------|---------|---------|
| `~/.prowlrbot/` | Config, chats, skills, cron jobs, monitors | Yes |
| `~/.prowlrbot.secret/` | API keys (envs.json) | Yes, carefully |

Backup:

```bash
prowlr backup create --include-secrets
# Saves to ~/.prowlrbot/backups/<timestamp>.tar.gz
```

Restore:

```bash
prowlr backup restore /path/to/backup.tar.gz
```
