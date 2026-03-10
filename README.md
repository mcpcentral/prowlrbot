<p align="center">
  <img src="console/public/logo.png" alt="ProwlrBot" width="120" />
</p>

<h1 align="center">ProwlrBot</h1>
<p align="center"><strong>Always watching. Always ready.</strong></p>

<p align="center">
  <a href="https://github.com/mcpcentral/prowlrbot/actions"><img src="https://img.shields.io/github/actions/workflow/status/mcpcentral/prowlrbot/ci.yml?branch=main&style=flat-square" alt="CI" /></a>
  <a href="https://pypi.org/project/prowlrbot/"><img src="https://img.shields.io/pypi/v/prowlrbot?style=flat-square" alt="PyPI" /></a>
  <a href="https://github.com/mcpcentral/prowlrbot/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcpcentral/prowlrbot?style=flat-square" alt="License" /></a>
  <a href="https://github.com/mcpcentral/prowlrbot/stargazers"><img src="https://img.shields.io/github/stars/mcpcentral/prowlrbot?style=flat-square" alt="Stars" /></a>
  <a href="https://mcpcentral.github.io/prowlr-docs"><img src="https://img.shields.io/badge/docs-website-blue?style=flat-square" alt="Docs" /></a>
</p>

<p align="center">
  <a href="#-30-second-install">Install</a> · <a href="#-what-makes-prowlrbot-different">Why ProwlrBot</a> · <a href="docs/README.md">Full Docs</a> · <a href="docs/blog/">Blog</a> · <a href="https://github.com/mcpcentral/prowlrbot/issues">Issues</a>
</p>

---

## 30-Second Install

```bash
pip install prowlrbot
prowlr init --defaults
prowlr env set OPENAI_API_KEY sk-your-key
prowlr app
```

Open **http://localhost:8088** — your agent is live.

> **No API key?** Run locally with Ollama: `prowlr init --defaults && prowlr app` — ProwlrBot auto-detects local models.

---

## What Makes ProwlrBot Different

Most AI agent platforms give you **one agent in one terminal**. ProwlrBot gives you an **operations center**.

<table>
<tr>
<td width="50%">

### The Problem

You open 3 Claude Code terminals to parallelize work. Terminal A edits `models.py`. Terminal B edits `models.py`. Git conflict. Wasted work. You babysit agents instead of shipping.

</td>
<td width="50%">

### The ProwlrBot Solution

Agents share a **war room** — a mission board with file locks, shared context, and real-time coordination. Terminal A claims `models.py`. Terminal B sees the lock and works on something else. Zero conflicts.

</td>
</tr>
</table>

### Feature Comparison

| Capability | ProwlrBot | Manus | Devin | AutoGPT | Claude Code |
|:-----------|:---------:|:-----:|:-----:|:-------:|:-----------:|
| Multi-agent coordination | **War Room** | -- | -- | Basic | -- |
| Cross-machine execution | **Swarm** | -- | -- | -- | -- |
| Communication channels | **8** | 1 | 1 | 1 | 1 |
| AI providers | **7** | 1 | 1 | 2 | 1 |
| Smart model routing | **Yes** | -- | -- | -- | -- |
| Protocol support | **MCP+ACP+A2A** | -- | -- | -- | MCP |
| Web monitoring | **Yes** | -- | -- | -- | -- |
| Skills marketplace | **Yes** | -- | -- | Yes | -- |
| Open source | **Yes** | No | No | Yes | Yes |

---

## How It Works

```
                    YOU
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      Discord    Telegram    Console     ← 8 channels
          │          │          │
          └──────────┼──────────┘
                     ▼
             ChannelManager              ← queue + debounce
                     │
                     ▼
              AgentRunner                ← session management
                     │
                     ▼
           ProwlrBotAgent (ReAct)        ← reasoning loop
            ┌────┬────┬────┐
            ▼    ▼    ▼    ▼
         Tools Skills MCP Memory         ← capabilities
            │    │    │    │
            └────┼────┼────┘
                 ▼    ▼
         ┌───────────────────┐
         │   Smart Router    │           ← picks best model
         ├───────────────────┤
         │ OpenAI │Anthropic │
         │ Groq   │ Z.ai    │
         │ Ollama │ llama   │
         │ MLX    │         │
         └───────────────────┘
```

**One message in. Best model picked. Tools executed. Response out.**

---

## The Stack At A Glance

<table>
<tr><td>

### Providers (7)
| Provider | How |
|:---------|:----|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Groq | `GROQ_API_KEY` |
| Z.ai | `ZAI_API_KEY` |
| Ollama | Local (no key) |
| llama.cpp | Local (no key) |
| MLX | Local (Apple Silicon) |

Smart Router scores: `cost × w₁ + speed × w₂ + availability × w₃` → picks the winner.

</td><td>

### Channels (8)
| Channel | Setup |
|:--------|:------|
| Console | Built-in at `:8088` |
| Discord | `prowlr channels add discord` |
| Telegram | `prowlr channels add telegram` |
| DingTalk | `prowlr channels add dingtalk` |
| Feishu | `prowlr channels add feishu` |
| QQ | `prowlr channels add qq` |
| iMessage | `prowlr channels add imessage` |
| Custom | Drop into `~/.prowlrbot/custom_channels/` |

</td></tr>
<tr><td>

### Tools (Built-in)
| Tool | What it does |
|:-----|:-------------|
| `shell` | Execute commands |
| `file_io` | Read/write files |
| `browser` | Open URLs, automate |
| `screenshot` | Capture screens |
| `send_file` | Send files via channel |
| `memory_search` | Search agent memory |

</td><td>

### Skills (Extensible)
| Skill | Enable with |
|:------|:------------|
| PDF processing | `prowlr skills enable pdf` |
| Word documents | `prowlr skills enable docx` |
| Spreadsheets | `prowlr skills enable xlsx` |
| Presentations | `prowlr skills enable pptx` |
| News feeds | `prowlr skills enable news` |
| Browser (visible) | `prowlr skills enable browser_visible` |
| Email (Himalaya) | `prowlr skills enable himalaya` |
| Cron scheduling | `prowlr skills enable cron` |

</td></tr>
</table>

---

## Multi-Agent War Room

> **The killer feature.** Multiple AI agents coordinating in real-time without stepping on each other.

### Quick Setup

```bash
# Install
git clone https://github.com/mcpcentral/prowlrbot.git && cd prowlrbot && pip install -e .

# Tell your Claude Code agent:
# "Set up the war room using https://github.com/mcpcentral/prowlrbot/blob/main/INSTALL.md"
# It handles everything.
```

### What You Get

```
╔══════════════════════════════════════════════════════════════╗
║                      MISSION BOARD                          ║
╠════╦══════════════════════╦═══════════╦══════════════════════╣
║ ID ║ Task                 ║ Agent     ║ Status               ║
╠════╬══════════════════════╬═══════════╬══════════════════════╣
║  1 ║ Build auth API       ║ backend   ║ In Progress          ║
║  2 ║ Login page           ║ frontend  ║ In Progress          ║
║  3 ║ Write auth tests     ║ tester    ║ Waiting (locked)     ║
║  4 ║ API documentation    ║ --        ║ Available            ║
╚════╩══════════════════════╩═══════════╩══════════════════════╝

Locked Files:
  src/api/auth.py ─── backend (Task #1)
  src/api/models.py ─── backend (Task #1)
  src/components/Login.tsx ─── frontend (Task #2)

Shared Findings:
  backend: "Auth requires JWT — using PyJWT with RS256"
  frontend: "Using shadcn/ui form components for login"
```

### 13 Coordination Tools

| Tool | Purpose | When to use |
|:-----|:--------|:------------|
| `check_mission_board` | See all tasks and owners | Before starting work |
| `claim_task` | Create task + lock files atomically | When starting a task |
| `update_task` | Post progress notes | During work |
| `complete_task` | Mark done + release locks | When finished |
| `fail_task` | Mark failed + release locks | When blocked |
| `lock_file` | Lock additional files | Need more files mid-task |
| `unlock_file` | Release a specific lock | No longer need a file |
| `check_conflicts` | Check if files are available | Before editing |
| `get_agents` | See who's connected | Coordinate with team |
| `broadcast_status` | Message all agents | Announce blockers/decisions |
| `share_finding` | Store a discovery | Found something others need |
| `get_shared_context` | Read team findings | Learn what others discovered |
| `get_events` | See recent activity | Catch up on what happened |

### Cross-Machine Support

Agents on different machines? The HTTP bridge connects them:

```
Mac (host)                    WSL (remote)
┌─────────────┐               ┌─────────────┐
│ Agent A     │               │ Agent B     │
│ Agent C     │               │ Agent D     │
│             │               │             │
│ SQLite DB   │◄──HTTP:8099──►│ Bridge      │
│ (war room)  │   (bridge)    │ Client      │
└─────────────┘               └─────────────┘
```

Different networks? Use [Tailscale](docs/guides/cross-network-setup.md#option-1-tailscale-recommended), [Cloudflare Tunnel](docs/guides/cross-network-setup.md#option-2-cloudflare-tunnel), or [SSH tunnel](docs/guides/cross-network-setup.md#option-4-ssh-reverse-tunnel).

> **Full guide:** [docs/guides/cross-network-setup.md](docs/guides/cross-network-setup.md)

---

## Web Monitoring

ProwlrBot watches websites and APIs for changes — then notifies you or triggers agent actions.

```bash
# Monitor a webpage for changes
prowlr monitor add https://example.com/pricing --interval 1h

# Monitor an API endpoint
prowlr monitor add https://api.example.com/v2/status --type api --interval 5m

# List active monitors
prowlr monitor list

# View change history
prowlr monitor history
```

**How it works:** Content diffing → change detection → webhook/channel notifications. Useful for price tracking, competitor monitoring, API status, content updates.

---

## Cron Jobs

Schedule your agents to run tasks automatically:

```bash
# Run every morning at 9 AM
prowlr cron add "Check email and summarize" --schedule "0 9 * * *"

# Run every 30 minutes
prowlr cron add "Monitor competitors" --interval 30m

# Run once at a specific time
prowlr cron add "Send weekly report" --schedule "0 17 * * FRI"
```

---

## REST API

ProwlrBot exposes a full API at `http://localhost:8088/api`:

```bash
# Set an API token
prowlr env set PROWLRBOT_API_TOKEN your-secret-token

# Then use it
curl -H "Authorization: Bearer your-secret-token" http://localhost:8088/api/agents
```

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/api/version` | GET | Server version |
| `/api/agents` | GET/POST | List or create agents |
| `/api/agents/{id}` | GET/PUT/DELETE | Manage a specific agent |
| `/api/channels` | GET/POST | Channel management |
| `/api/skills` | GET | Available skills |
| `/api/cron` | GET/POST | Cron job management |
| `/api/providers` | GET | Available AI providers |
| `/api/config` | GET/PUT | System configuration |
| `/ws/dashboard` | WebSocket | Real-time event stream |

---

## MCP Integration

Connect any MCP server — tools appear instantly:

```json
// ~/.prowlrbot/config.json
{
  "mcp": {
    "servers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
      },
      "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": { "GITHUB_TOKEN": "ghp_..." }
      }
    }
  }
}
```

Hot-reload: edit config → tools update automatically. No restart needed.

---

## Local Models (No Cloud Required)

Run everything on your machine:

| Backend | Best For | Install | Run |
|:--------|:---------|:--------|:----|
| **Ollama** | Cross-platform, easy | [ollama.ai](https://ollama.ai) | `ollama pull llama3.2 && prowlr app` |
| **llama.cpp** | GGUF models, CPU/GPU | `pip install 'prowlrbot[llamacpp]'` | Point to model file in config |
| **MLX** | Apple Silicon M1-M4 | `pip install 'prowlrbot[mlx]'` | Fastest on Mac |

ProwlrBot auto-detects local models. No API keys. No cloud. Your data stays on your machine.

---

## Project Structure

```
prowlrbot/
├── src/prowlrbot/
│   ├── agents/            # ReAct agent, tools, skills, memory
│   │   ├── react_agent.py # Core agent (ProwlrBotAgent)
│   │   ├── model_factory  # Provider → model creation
│   │   ├── tools/         # shell, file_io, browser, screenshot
│   │   ├── skills/        # Built-in skill packs
│   │   └── memory/        # Conversation memory + compaction
│   ├── app/
│   │   ├── _app.py        # FastAPI app + lifespan
│   │   ├── channels/      # Discord, Telegram, etc.
│   │   ├── crons/         # APScheduler-based scheduling
│   │   ├── mcp/           # MCP client lifecycle
│   │   └── routers/       # REST API endpoints
│   ├── cli/               # Click CLI → `prowlr` command
│   ├── config/            # Pydantic models + hot-reload
│   ├── providers/         # Registry, detector, smart router
│   ├── monitor/           # Web/API change detection
│   ├── hub/               # ProwlrHub war room (MCP server)
│   └── envs/              # Encrypted secret store
├── console/               # React 18 + Vite + Ant Design
├── swarm/                 # Cross-machine Redis execution
├── plugins/               # Claude Code plugins
├── docs/                  # Documentation hub
│   ├── blog/              # Humanized posts + updates
│   ├── guides/            # Setup + troubleshooting guides
│   ├── protocols/         # ROAR protocol specs
│   ├── plans/             # Design documents
│   └── README.md          # Documentation index
└── website/               # GitHub Pages docs site
```

---

## Documentation

> **Start here:** [docs/README.md](docs/README.md) — the documentation hub with links to everything.

| What you need | Where to go |
|:--------------|:------------|
| First-time setup | [Quick Start](#-30-second-install) (above) |
| War room setup | [INSTALL.md](INSTALL.md) |
| Cross-machine networking | [Cross-Network Guide](docs/guides/cross-network-setup.md) |
| Architecture deep-dive | [CLAUDE.md](CLAUDE.md) |
| ROAR Protocol | [Protocol Specs](docs/protocols/ROAR-SPEC.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Security policy | [SECURITY.md](SECURITY.md) |
| Blog & updates | [docs/blog/](docs/blog/) |
| Full docs site | [mcpcentral.github.io/prowlr-docs](https://mcpcentral.github.io/prowlr-docs) |

---

## Ecosystem

<table>
<tr>
<td align="center" width="20%">
<a href="https://github.com/mcpcentral/prowlrbot"><strong>ProwlrBot</strong></a><br/>
<sub>Core agent platform</sub>
</td>
<td align="center" width="20%">
<a href="https://github.com/mcpcentral/roar-protocol"><strong>ROAR Protocol</strong></a><br/>
<sub>Agent communication</sub>
</td>
<td align="center" width="20%">
<a href="https://github.com/mcpcentral/prowlr-marketplace"><strong>Marketplace</strong></a><br/>
<sub>Skills & agents</sub>
</td>
<td align="center" width="20%">
<a href="https://mcpcentral.github.io/prowlr-docs"><strong>Docs</strong></a><br/>
<sub>Guides & reference</sub>
</td>
<td align="center" width="20%">
<a href="https://github.com/mcpcentral/agentverse"><strong>AgentVerse</strong></a><br/>
<sub>Virtual agent world</sub>
</td>
</tr>
</table>

---

## Development

```bash
git clone https://github.com/mcpcentral/prowlrbot.git
cd prowlrbot
pip install -e ".[dev]"
pytest                                          # run all tests
pre-commit install && pre-commit run --all-files  # lint + format

# Frontend
cd console && npm ci && npm run build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for commit conventions, skill structure, and PR guidelines.

---

<p align="center">
  <strong>ProwlrBot</strong> — Always watching. Always ready.<br/><br/>
  <a href="docs/README.md">Docs</a> ·
  <a href="docs/blog/">Blog</a> ·
  <a href="https://github.com/mcpcentral/prowlrbot/issues">Issues</a> ·
  <a href="https://github.com/mcpcentral/prowlr-marketplace">Marketplace</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>
