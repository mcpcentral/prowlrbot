# ProwlrBot War Room Setup

> **Just tell your Claude Code agent:**
>
> *"Set up the war room using https://github.com/prowlrbot/prowlrbot/blob/main/INSTALL.md"*
>
> Your agent will clone the repo, ask you a few questions, configure everything, and verify the connection. You don't need to do anything manually.

---

## One-Command Wizard (optional)

If you prefer to run a guided wizard yourself instead of having Claude handle it,
use the bundled script from inside the `prowlrbot` repo:

```bash
cd prowlrbot
./scripts/setup-warroom.sh
```

The wizard will:

- check Python and the `prowlrbot` install
- initialize `~/.prowlrbot/warroom.db`
- ask for an **agent name** and **capabilities**
- print the exact `.mcp.json` snippet you can paste into your project

You can then restart Claude Code and verify with `check_mission_board`.

---

## For the Agent

You are setting up ProwlrHub — a shared war room that connects multiple Claude Code terminals so they can coordinate instead of stepping on each other's work.

Follow these steps exactly. Ask the user questions where indicated.

### Step 1: Clone and install

```bash
git clone https://github.com/prowlrbot/prowlrbot.git
cd prowlrbot
pip install -e .
```

If the repo already exists, `cd` into it and run `git pull && pip install -e .` instead.

### Step 2: Ask the user 3 questions

**Question 1: "What should I call this agent?"**
- Examples: `architect`, `frontend`, `security`, `marketplace-dev`, `docs`
- This name shows up on the mission board so other agents know who's who
- Default if they skip: `claude-agent`

**Question 2: "What are this agent's capabilities?"**
- Comma-separated list: `python,api,database` or `react,typescript,css` or `security,testing`
- This helps with task matching — agents with the right capabilities get the right work
- Default if they skip: `general`

**Question 3: "Are you connecting from the same machine, or a different machine (like WSL)?"**
- **Same machine** → use local mode (no bridge needed)
- **Different machine** → need the bridge URL. Ask: "What's the bridge URL? (e.g., http://192.168.12.21:8099)"

### Step 3: Register the MCP server

**If same machine (recommended — all agents share one war room):**

```bash
claude mcp add prowlr-hub -s local \
  -e PYTHONPATH="$(pwd)/src" \
  -e PROWLR_AGENT_NAME="<agent_name>" \
  -e PROWLR_CAPABILITIES="<capabilities>" \
  -e PROWLR_HUB_URL="http://localhost:8099" \
  -- python3 -m prowlrbot.hub
```

> **Important:** Always include `PROWLR_HUB_URL` even on the same machine. Without it, each terminal creates its own isolated database and agents can't see each other's tasks.

**If different machine (remote mode):**

```bash
claude mcp add prowlr-hub -s local \
  -e PYTHONPATH="$(pwd)/src" \
  -e PROWLR_AGENT_NAME="<agent_name>" \
  -e PROWLR_CAPABILITIES="<capabilities>" \
  -e PROWLR_HUB_URL="<bridge_url>" \
  -- python3 -m prowlrbot.hub
```

Replace `<agent_name>`, `<capabilities>`, and `<bridge_url>` with the user's answers.

### Step 4: Tell the user to restart Claude Code

Say: "Restart Claude Code now (not just the conversation — fully quit and reopen). The war room tools will be available when you come back."

### Step 5: Verify (after restart)

Call `check_mission_board`. If you see the mission board (even if empty), you're connected. Tell the user:

"You're connected to the war room. You now have 13 coordination tools. Use `/board` to see the mission board, `/claim` to grab a task, `/team` to see other agents."

If it fails, check:
1. Is `PYTHONPATH` pointing to the `src/` directory inside the prowlrbot clone?
2. Did the user fully restart Claude Code?
3. Run `claude mcp list` to see if `prowlr-hub` is registered

---

## Starting the Bridge (for cross-machine setups)

If agents are on different machines (Mac + WSL, multiple computers), one machine needs to run the bridge.

**On the host machine (the one that owns the database):**

```bash
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge
```

This starts on port 8099. Get the host IP:
- macOS: `ipconfig getifaddr en0`
- Linux: `hostname -I | awk '{print $1}'`

Remote agents connect with `PROWLR_HUB_URL=http://<host_ip>:8099`.

**If machines are on different networks** (guest WiFi, VPN, etc), see the [Cross-Network Setup Guide](docs/guides/cross-network-setup.md) for Tailscale, Cloudflare Tunnel, and other tunnel options.

---

## What You Get

Once connected, every agent has these tools:

| Tool | What it does |
|------|-------------|
| `check_mission_board` | See all tasks, owners, and progress |
| `claim_task` | Create and claim a task, atomically lock files |
| `update_task` | Post progress notes for the team |
| `complete_task` | Mark done, release all file locks |
| `fail_task` | Mark failed, release locks |
| `lock_file` / `unlock_file` | Advisory file locking |
| `check_conflicts` | Check if files are locked before editing |
| `get_agents` | See who's connected |
| `broadcast_status` | Send a message to all agents |
| `share_finding` | Store a discovery for other agents |
| `get_shared_context` | Read what other agents have found |
| `get_events` | See recent war room activity |

And these slash commands: `/board`, `/claim`, `/team`, `/broadcast`, `/warroom`

---

## War Room Protocol

Add this to your project's `CLAUDE.md` to make agents follow the protocol automatically:

```markdown
## War Room

You are connected to ProwlrHub. Before any work:
1. `check_mission_board` — see what's available
2. `get_agents` — see who else is working
3. `check_conflicts` on files you'll edit
4. `claim_task` with file scopes before editing
5. `share_finding` when you discover something useful
6. `complete_task` when done — releases all locks
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "prowlr-hub exists in multiple scopes" | Remove from one scope: `claude mcp remove prowlr-hub -s project` then re-add with `-s local` (no `-c`). See [War Room MCP debug](docs/guides/war-room-mcp-debug.md). |
| "No module named prowlrbot" | `PYTHONPATH` must point to `prowlrbot/src/` (e.g. `/home/anon/dev/prowlrbot/src`). No `-c` flag for `claude mcp add` — run from repo dir or use absolute path in env. |
| Tools not appearing | Restart Claude Code fully, check `claude mcp list` |
| "Database is locked" | Kill stale processes: `ps aux \| grep prowlrbot.hub` |
| Bridge connection refused | Check bridge is running: `curl http://HOST:8099/health` |
| Agent not on board | Call any tool — agents auto-register on first use |
| Board empty / agents can't see tasks | Add `PROWLR_HUB_URL=http://localhost:8099` to MCP config — without it each terminal gets its own DB |
| Can't reach bridge from WSL | Check firewall, try `ping HOST_IP` first |
| Different networks | Use Tailscale or Cloudflare Tunnel — see [guide](docs/guides/cross-network-setup.md) |

---

## Links

- [War Room MCP debug](docs/guides/war-room-mcp-debug.md) — Fix duplicate scopes, wrong PYTHONPATH, `-c` errors
- [Cross-Network Setup Guide](docs/guides/cross-network-setup.md) — Tailscale, Cloudflare, ngrok, SSH tunnels
- [War Room Protocol](src/prowlrbot/hub/SKILL.md) — The 7 Iron Rules
- [Hub Architecture](src/prowlrbot/hub/README.md) — Database schema, bridge API, developer guide
- [GitHub](https://github.com/prowlrbot/prowlrbot) — Source code
- [Issues](https://github.com/prowlrbot/prowlrbot/issues) — Bug reports
