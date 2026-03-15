# ProwlrHub — War Room Multi-Agent Coordination

**Connect multiple Claude Code terminals into one coordinated team.**

ProwlrHub is an MCP (Model Context Protocol) server that gives every Claude Code instance in your project shared awareness: who's working on what, which files are locked, what's been discovered, and what still needs doing.

Part of the [ProwlrBot](https://github.com/prowlrbot/prowlrbot) ecosystem. Built on the [ROAR Protocol](https://github.com/ProwlrBot/roar-protocol) for agent identity and communication.

---

## Why?

When you run 4 Claude Code terminals on the same codebase, they can't see each other. They'll edit the same files, duplicate research, and step on each other's work. ProwlrHub fixes this with a shared coordination layer that all instances read/write through atomic transactions.

### What it solves

| Without ProwlrHub | With ProwlrHub |
|--------------------|----------------|
| Agents edit the same file simultaneously | Advisory file locks prevent conflicts |
| Duplicate research across terminals | Shared findings store lets agents share discoveries |
| No visibility into who's doing what | Mission board shows all tasks, owners, and progress |
| Silent failures when agents conflict | Atomic task claiming prevents race conditions |
| No coordination between Mac and WSL | HTTP bridge enables cross-machine war rooms |

---

## Quick Start

> **Shortest path (Claude does it for you):**
> Tell your Claude Code agent in this project:
> *"Connect this project to the ProwlrBot war room using
> https://github.com/prowlrbot/prowlrbot/blob/main/INSTALL.md.
> The prowlrbot repo lives at `~/dev/prowlrbot`."*
>
> The agent will clone/update the repo if needed, ask for an agent name + capabilities,
> configure the MCP server, and verify the connection.

### Common Setups

#### Single machine (all terminals on same OS)

If you prefer to wire it up yourself:

1. Install once per machine:

   ```bash
   git clone https://github.com/prowlrbot/prowlrbot.git
   cd prowlrbot
   pip install -e .
   ```

2. In your **project** root, create or update `.mcp.json`:

   ```jsonc
   {
     "mcpServers": {
       "prowlr-hub": {
         "command": "python3",
         "args": ["-m", "prowlrbot.hub"],
         "cwd": "/path/to/prowlrbot",
         "env": {
           "PYTHONPATH": "/path/to/prowlrbot/src",
           "PROWLR_AGENT_NAME": "my-agent",
           "PROWLR_CAPABILITIES": "code,review"
         }
       }
     }
   }
   ```

3. Fully restart Claude Code and ask your agent to call `check_mission_board`.
   If you see the board (even if empty), this terminal is in the War Room.

#### Mac + WSL (bridge mode)

On the **host** machine that owns the database (for example, macOS):

```bash
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge
# Bridge listens on http://<host-ip>:8099
```

On the **remote** terminal (for example, WSL), add `PROWLR_HUB_URL`:

```jsonc
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
        "PROWLR_HUB_URL": "http://<host-ip>:8099"
      }
    }
  }
}
```

Restart Claude on both sides and run `check_mission_board` — you should see a single shared mission board.

### Manual Setup

#### 1. Clone and install

```bash
git clone https://github.com/prowlrbot/prowlrbot.git
cd prowlrbot
pip install -e .
```

#### 2. Add to `.mcp.json`

Create or update `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "prowlr-hub": {
      "command": "python3",
      "args": ["-m", "prowlrbot.hub"],
      "cwd": "/path/to/prowlrbot",
      "env": {
        "PYTHONPATH": "/path/to/prowlrbot/src",
        "PROWLR_AGENT_NAME": "my-agent",
        "PROWLR_CAPABILITIES": "code,review"
      }
    }
  }
}
```

#### 3. Restart Claude Code

Each terminal auto-spawns its own MCP server process. On the same machine, all share `~/.prowlrbot/warroom.db`.

#### 4. Verify

Ask your agent to use `check_mission_board`. If you see the board, you're connected.

---

## Available Tools (13)

Every connected Claude Code terminal gets these war room tools:

### Mission Board

| Tool | What it does |
|------|-------------|
| `check_mission_board` | See all tasks — status, owner, priority, file scopes, progress notes |
| `claim_task` | Create and/or claim a task. Atomically locks all file scopes. Fails if any file is already locked |
| `update_task` | Post a progress note on your current task. Other agents see this on the board |
| `complete_task` | Mark your task as done. Releases all file locks automatically |
| `fail_task` | Mark a task as failed with a reason. Releases all locks |

### File Coordination

| Tool | What it does |
|------|-------------|
| `lock_file` | Advisory lock on a file path. Other agents see it's taken and back off |
| `unlock_file` | Release a file lock when you're done |
| `check_conflicts` | Check if any of these files are locked before you start editing |

### Team Awareness

| Tool | What it does |
|------|-------------|
| `get_agents` | See all connected agents — name, capabilities, status, current task |
| `broadcast_status` | Send a message to all agents. Use when blocked, need help, or have news |
| `share_finding` | Store a key-value finding. Other agents can query it before starting research |
| `get_shared_context` | Read findings shared by other agents. Check before duplicating work |
| `get_events` | See recent war room activity — claims, completions, broadcasts, findings |

---

## Two Operating Modes

### Local Mode (same machine)

```
Terminal 1 ──┐
Terminal 2 ──┤── SQLite WAL ──── ~/.prowlrbot/warroom.db
Terminal 3 ──┘
```

All terminals on the same machine share one SQLite database. No configuration needed beyond `.mcp.json`. SQLite's WAL (Write-Ahead Logging) enables concurrent reads with serialized writes. Atomic transactions prevent race conditions.

### Remote Mode (cross-machine: Mac + WSL)

```
Mac Terminal 1 ──┐                            ┌── WSL Terminal 1
Mac Terminal 2 ──┤── SQLite ── HTTP Bridge ───┤── WSL Terminal 2
Mac Terminal 3 ──┘     :8099                  └── Linux Terminal 1
```

SQLite can't be shared across Mac and WSL filesystems safely (lock corruption). The HTTP bridge solves this by exposing all war room operations over REST.

#### Start the bridge (on the database host)

```bash
cd prowlrbot
PYTHONPATH=src python3 -m prowlrbot.hub.bridge
# Starts on port 8099
```

Verify: `curl http://localhost:8099/health`

#### Configure remote terminals

Add `PROWLR_HUB_URL` to the remote terminal's `.mcp.json`:

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
        "PROWLR_HUB_URL": "http://<host-ip>:8099"
      }
    }
  }
}
```

When `PROWLR_HUB_URL` is set, the MCP server automatically routes all operations through the HTTP bridge instead of local SQLite. The remote client uses only stdlib (`urllib`) — no external dependencies.

#### Bridge environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROWLR_HUB_DB` | `~/.prowlrbot/warroom.db` | Database file path |
| `PROWLR_BRIDGE_HOST` | `0.0.0.0` | Bind address |
| `PROWLR_BRIDGE_PORT` | `8099` | HTTP port |

---

## Architecture

### Module Structure

```
src/prowlrbot/hub/
├── __init__.py         # Package docstring
├── __main__.py         # Entry point: python -m prowlrbot.hub
├── db.py               # SQLite schema (7 tables, 5 indexes, WAL mode)
├── engine.py           # Core coordination logic (all business rules)
├── mcp_server.py       # MCP stdio server (13 tools, local + remote routing)
├── bridge.py           # HTTP bridge server (FastAPI, cross-machine)
├── remote_client.py    # HTTP client for bridge mode (stdlib only)
├── SKILL.md            # War room protocol rules for Claude Code agents
└── README.md           # This file
```

### Three Layers

```
┌──────────────────────────────────────────────────┐
│   MCP Server (mcp_server.py)                     │
│   13 tools, auto-registration, remote routing    │
│   Detects PROWLR_HUB_URL → routes to bridge     │
├──────────────────────────────────────────────────┤
│   War Room Engine (engine.py)                    │
│   Rooms, Agents, Tasks, Locks, Events, Context   │
│   All operations atomic via SQLite transactions  │
├──────────────────────────────────────────────────┤
│   SQLite Database (db.py)                        │
│   WAL mode, busy_timeout=5s, foreign keys ON     │
│   7 tables, 5 indexes, check_same_thread=False   │
└──────────────────────────────────────────────────┘
        │                        │
    [Local Mode]           [Remote Mode]
    Direct SQLite       HTTP Bridge → SQLite
```

### Database Schema

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `rooms` | War room instances | room_id, name, mode, auth_policy |
| `agents` | Connected Claude Code instances | agent_id, name, capabilities, status, current_task_id |
| `nodes` | Physical machines | node_id, hostname, platform, health |
| `tasks` | Mission board work items | task_id, title, status, owner, file_scopes, priority |
| `file_locks` | Advisory file locks | file_path, agent_id, lock_token, branch |
| `events` | Audit log | type, agent_id, task_id, payload, timestamp |
| `shared_context` | Key-value discovery store | key, agent_id, value |

### Atomic Task Claiming

The most critical operation. When an agent claims a task, the engine runs a single SQLite transaction:

```sql
BEGIN TRANSACTION;
  -- 1. Verify task is still available
  SELECT * FROM tasks WHERE task_id=? AND status='pending';

  -- 2. Verify all file scopes are unlocked (or owned by this agent)
  SELECT * FROM file_locks
  WHERE file_path IN (...) AND room_id=? AND agent_id != ?;

  -- 3. If both pass: claim + lock + update status (all or nothing)
  UPDATE tasks SET status='claimed', owner_agent_id=? WHERE task_id=?;
  INSERT INTO file_locks (file_path, room_id, agent_id, lock_token) VALUES (...);
  UPDATE agents SET status='working', current_task_id=? WHERE agent_id=?;
COMMIT;
```

If ANY step fails, the entire transaction rolls back. No partial claims, no orphan locks, no race conditions.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROWLR_AGENT_NAME` | `claude-{hostname}-{pid}` | Human-readable name for this terminal |
| `PROWLR_CAPABILITIES` | `general` | Comma-separated: `python,testing,frontend` |
| `PROWLR_HUB_DB` | `~/.prowlrbot/warroom.db` | Custom database path |
| `PROWLR_HUB_URL` | *(empty)* | Set to bridge URL for remote mode |

### Naming Your Agents

Give each terminal a role by setting `PROWLR_AGENT_NAME`:

```json
{
  "prowlr-hub": {
    "env": {
      "PROWLR_AGENT_NAME": "backend-architect",
      "PROWLR_CAPABILITIES": "python,api,database,architecture"
    }
  }
}
```

Example team setup:

| Agent Name | Capabilities | Role |
|------------|-------------|------|
| `architect` | `python,api,architecture` | System design, API routes, database schema |
| `frontend` | `typescript,react,css,ui` | Console UI, components, styling |
| `security` | `security,testing,audit` | Vulnerability scanning, auth, hardening |
| `docs` | `docs,markdown,git,readme` | Documentation, guides, changelogs |
| `devops` | `docker,ci,deploy,monitoring` | Deployment, CI/CD, infrastructure |

---

## The War Room Protocol

Every agent follows these rules (enforced by `SKILL.md`):

### 7 Iron Rules

1. **ALWAYS check before working.** Call `check_mission_board()` before any task.
2. **If someone claimed it, don't touch it.** Help them or pick something else.
3. **Claim before you code.** Call `claim_task()` with file scopes BEFORE editing.
4. **If claim fails, back off.** Never force through a failed claim.
5. **Lock before you edit.** Use `lock_file()` for files outside your task scope.
6. **Share what you find.** Use `share_finding()` so others don't redo research.
7. **Complete when done.** Call `complete_task()` to release all locks.

### Recommended Workflow

```
1. check_mission_board()         → See what's available
2. get_agents()                  → See who's working on what
3. check_conflicts(my_files)     → Verify files are free
4. claim_task(title, files)      → Lock files, claim work
5. ... do the work ...
6. update_task(id, "progress")   → Keep team informed
7. share_finding(key, value)     → Share discoveries
8. complete_task(id, "summary")  → Release locks, mark done
```

---

## Safety Features

| Feature | How it works |
|---------|-------------|
| **Dead agent sweep** | Agents that haven't heartbeated in 5 minutes are disconnected. All their locks release automatically |
| **Disconnect cleanup** | When an agent disconnects, in-progress tasks return to pending for others to claim |
| **Branch-aware locking** | File locks include git branch — agents on different branches don't conflict |
| **Event audit log** | Every action (claim, complete, broadcast, finding) is logged with agent ID and timestamp |
| **Graceful degradation** | If the bridge goes down, local agents continue working independently. Reconnect when bridge returns |

---

## Testing

```bash
# All hub tests (engine + bridge E2E)
PYTHONPATH=src python3 -m pytest tests/hub/ -v

# 44 tests covering:
# Engine tests (32):
#   - Room management (4)
#   - Agent lifecycle (5)
#   - Task management (11)
#   - File locking (5)
#   - Shared context (3)
#   - Events (3)
#   - Dead agent sweep (1)
# Bridge E2E tests (12):
#   - Health check
#   - Agent registration
#   - Mission board operations
#   - Task claiming through bridge
#   - Shared context through bridge
#   - File locking through bridge
#   - Broadcast and events through bridge

# ROAR protocol tests
PYTHONPATH=src python3 -m pytest tests/protocols/test_roar_transports.py -v
# 18 tests covering server, client, transport selection, signing
```

---

## For Developers

### Adding New Tools

1. Add tool definition to `TOOLS` dict in `mcp_server.py` (name, description, inputSchema)
2. Add handler case in `handle_tool_call()` (local mode)
3. Add handler case in `_handle_remote_tool()` (remote mode)
4. Add engine method in `engine.py` (business logic)
5. Add bridge endpoint in `bridge.py` (HTTP bridge)
6. Add remote client method in `remote_client.py` (HTTP client)
7. Add tests in `tests/hub/test_engine.py` and `tests/hub/test_bridge_e2e.py`

### Database Migrations

The schema uses `CREATE TABLE IF NOT EXISTS` — safe to add new tables/indexes. For column changes, add a migration function in `db.py` that runs after `init_db()`.

### HTTP Bridge API

The bridge exposes all operations as REST endpoints:

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Server health + room/agent/task counts |
| POST | `/register` | `{name, capabilities}` | Register a new agent |
| POST | `/heartbeat/{agent_id}` | `{}` | Keep agent alive |
| GET | `/board?status=` | — | Get mission board (optional status filter) |
| POST | `/claim/{agent_id}` | `{title, task_id, file_scopes, ...}` | Claim or create+claim a task |
| POST | `/update/{agent_id}` | `{task_id, progress_note}` | Update task progress |
| POST | `/complete/{agent_id}` | `{task_id, summary}` | Complete a task |
| POST | `/fail/{agent_id}` | `{task_id, reason}` | Fail a task |
| POST | `/lock/{agent_id}` | `{path}` | Lock a file |
| POST | `/unlock/{agent_id}` | `{path}` | Unlock a file |
| POST | `/conflicts` | `{paths}` | Check for file conflicts |
| GET | `/agents` | — | List connected agents |
| POST | `/broadcast/{agent_id}` | `{message}` | Broadcast to all agents |
| POST | `/findings/{agent_id}` | `{key, value}` | Share a finding |
| GET | `/context?key=` | — | Get shared context |
| GET | `/events?limit=&event_type=` | — | Get recent events |

---

## Related

- **[INSTALL.md](../../INSTALL.md)** — Full setup guide with wizard, one-liner, and manual options
- **[ROAR Protocol](../protocols/roar.py)** — Core agent communication protocol (5 layers)
- **[ROAR SDK](../protocols/sdk/)** — Client/server/router/streaming/crypto implementations
- **[roar-protocol repo](https://github.com/ProwlrBot/roar-protocol)** — Protocol specification
- **[prowlr-marketplace](https://github.com/ProwlrBot/prowlr-marketplace)** — Skill and agent marketplace
- **[prowlr-docs](https://github.com/ProwlrBot/prowlr-docs)** — Documentation site
