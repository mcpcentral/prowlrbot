# ProwlrBot Setup

> **Tell your Claude Code agent:** *"Connect me to the ProwlrBot war room using the instructions at https://github.com/mcpcentral/prowlrbot/blob/main/INSTALL.md"*
>
> Your agent will handle the rest.

---

## Quick Start (2 minutes)

```bash
git clone https://github.com/mcpcentral/prowlrbot.git
cd prowlrbot
pip install -e .
```

Then add the MCP server to your Claude Code. Pick **one** method:

### Option A: Setup Wizard (recommended)

```bash
./scripts/setup-warroom.sh
```

Names your agent, sets capabilities, configures `.mcp.json`, verifies the connection. Restart Claude Code when done.

### Option B: One-liner

```bash
claude mcp add prowlr-hub -s local -- python3 -m prowlrbot.hub
```

Then set the PYTHONPATH so the module is found:

```bash
claude mcp add prowlr-hub -s local -e PYTHONPATH="$(pwd)/src" -- python3 -m prowlrbot.hub
```

### Option C: Manual `.mcp.json`

Add this to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "prowlr-hub": {
      "command": "python3",
      "args": ["-m", "prowlrbot.hub"],
      "cwd": "/absolute/path/to/prowlrbot",
      "env": {
        "PYTHONPATH": "/absolute/path/to/prowlrbot/src",
        "PROWLR_AGENT_NAME": "my-agent",
        "PROWLR_CAPABILITIES": "code,review,testing"
      }
    }
  }
}
```

Replace `/absolute/path/to/prowlrbot` with your clone location.

## Verify

Restart Claude Code, then ask your agent:

```
Use the check_mission_board tool
```

You should see the mission board (empty or with tasks). If you see it, you're connected.

## Verify (CLI)

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | PYTHONPATH=src python3 -m prowlrbot.hub
```

You should see JSON with 13 tools listed.

---

## Multiple Terminals (Same Machine)

Every terminal on the same machine shares `~/.prowlrbot/warroom.db` automatically. Just give each a unique name:

**Terminal 1** — `.mcp.json`:
```json
"PROWLR_AGENT_NAME": "architect",
"PROWLR_CAPABILITIES": "python,api,architecture"
```

**Terminal 2** — `.mcp.json`:
```json
"PROWLR_AGENT_NAME": "frontend",
"PROWLR_CAPABILITIES": "typescript,react,css"
```

**Terminal 3** — `.mcp.json`:
```json
"PROWLR_AGENT_NAME": "security",
"PROWLR_CAPABILITIES": "security,testing,audit"
```

No bridge, no network config. They all see each other on the mission board instantly.

---

## Cross-Machine Setup (Mac + WSL)

SQLite can't be shared across Mac and WSL filesystems. ProwlrBot includes an HTTP bridge for this.

### Step 1: Start the bridge (on the machine with the database)

```bash
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge
```

The bridge starts on port `8099`. Verify:

```bash
curl http://localhost:8099/health
# → {"status":"ok","room_id":"...","agents":0,"tasks":0}
```

To run in background:

```bash
PYTHONPATH=src nohup python3 -m prowlrbot.hub.bridge &
```

### Step 2: Find the host IP

```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'
```

### Step 3: Configure remote terminals

On the remote machine (WSL, another Mac, Linux), set `PROWLR_HUB_URL` in `.mcp.json`:

```json
{
  "mcpServers": {
    "prowlr-hub": {
      "command": "python3",
      "args": ["-m", "prowlrbot.hub"],
      "cwd": "/path/to/prowlrbot",
      "env": {
        "PYTHONPATH": "/path/to/prowlrbot/src",
        "PROWLR_AGENT_NAME": "wsl-agent",
        "PROWLR_CAPABILITIES": "code,testing",
        "PROWLR_HUB_URL": "http://192.168.1.100:8099"
      }
    }
  }
}
```

Replace `192.168.1.100` with the host IP from Step 2.

### Step 4: Verify cross-machine

From the remote terminal, ask your agent:

```
Use the get_agents tool
```

You should see agents from **both** machines listed.

### Bridge Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROWLR_HUB_DB` | `~/.prowlrbot/warroom.db` | Database file path |
| `PROWLR_BRIDGE_HOST` | `0.0.0.0` | Bind address |
| `PROWLR_BRIDGE_PORT` | `8099` | HTTP port |

---

## What Your Agent Can Do

Once connected, your agent has these war room tools:

| Tool | Purpose |
|------|---------|
| `check_mission_board` | See all tasks, who owns what |
| `claim_task` | Grab a task, lock its files |
| `update_task` | Post progress updates |
| `complete_task` | Finish and release locks |
| `fail_task` | Mark failed, release locks |
| `lock_file` / `unlock_file` | Advisory file locking |
| `check_conflicts` | See if files are locked |
| `get_agents` | See who's connected |
| `broadcast_status` | Announce to all agents |
| `share_finding` | Share discoveries |
| `get_shared_context` | Read shared findings |
| `get_events` | See recent activity |

---

## Agent Instructions

Tell your Claude Code agent how to use the war room by adding this to your `CLAUDE.md`:

```markdown
## War Room Protocol

You are connected to ProwlrHub. Before starting any work:
1. Call `check_mission_board` to see what's available
2. Call `get_agents` to see who else is working
3. Call `check_conflicts` on files you plan to edit
4. Call `claim_task` to claim your work and lock files
5. Call `broadcast_status` when you hit milestones
6. Call `complete_task` when done — this releases all locks
```

---

## Troubleshooting

### "No module named prowlrbot"

The `PYTHONPATH` in your `.mcp.json` must point to the `src/` directory:

```bash
# Test it manually
PYTHONPATH=/path/to/prowlrbot/src python3 -c "import prowlrbot.hub; print('OK')"
```

### Tools not appearing in Claude Code

1. Ensure `.mcp.json` is in your **project root** (where you launched Claude Code)
2. Restart Claude Code fully (not just the conversation)
3. Run `claude mcp list` to see registered servers

### "Database is locked"

SQLite WAL mode handles most concurrency. If persistent:

```bash
# Find stuck processes
ps aux | grep prowlrbot.hub
# Kill stale ones
kill <pid>
```

### Bridge connection refused

```bash
# Check bridge is running
curl http://HOST:8099/health

# Check firewall (macOS)
sudo pfctl -sr | grep 8099

# Check WSL can reach Mac
ping HOST_IP
```

### Agent not on the board

Agents auto-register on first tool call. Just use any tool (`check_mission_board` is the easiest) and you'll appear.

---

## Requirements

- Python 3.10+
- Claude Code CLI
- Git
- FastAPI + uvicorn (for bridge mode only, installed with `pip install -e ".[dev]"`)

---

## Architecture

```
Terminal 1 ──┐
Terminal 2 ──┤── SQLite (same machine, automatic)
Terminal 3 ──┘

Terminal 4 (WSL) ──── HTTP Bridge ──── SQLite (cross-machine)
Terminal 5 (Mac) ───┘
```

All terminals see the same mission board, same agents, same shared context. Changes are instant.

---

## Links

- **Docs**: https://mcpcentral.github.io/prowlr-docs
- **GitHub**: https://github.com/mcpcentral/prowlrbot
- **Issues**: https://github.com/mcpcentral/prowlrbot/issues
- **War Room Protocol**: `src/prowlrbot/hub/SKILL.md`
- **ROAR Protocol**: `src/prowlrbot/protocols/roar/`
