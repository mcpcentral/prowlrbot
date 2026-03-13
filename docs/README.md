# ProwlrBot Documentation

> **Your map to everything.** Every guide, spec, and tutorial — linked and organized.

---

## Where Do I Start?

```
Are you...
│
├── New to ProwlrBot?
│   └── Start here ──────► Quick Start (README.md)
│                           pip install prowlrbot && prowlr app
│
├── Setting up multi-agent coordination?
│   └── War room setup ──► INSTALL.md
│                           One command, 3 questions, done.
│
├── Connecting agents across machines?
│   └── Networking ──────► Cross-Network Guide
│                           Tailscale / Cloudflare / SSH / ZeroTier
│
├── Building skills or contributing?
│   └── Developer guide ─► CONTRIBUTING.md + CLAUDE.md
│                           Architecture, conventions, PR process
│
├── Having issues?
│   └── Troubleshooting ──► docs/troubleshooting.md
│                            WSL, pip, ports, MCP, console fixes
│
└── Curious about the vision?
    └── Roadmap ─────────► Blog: What's Coming Next
                            Protocols, marketplace, AgentVerse
```

---

## Guides

Step-by-step walkthroughs. Follow them in order, skip what you don't need.

| # | Guide | What You'll Do | Time |
|:--|:------|:---------------|:-----|
| 1 | **[Quick Start](../README.md#-30-second-install)** | Install ProwlrBot, set API key, open console | 30 sec |
| 2 | **[Channel Setup](guides/channels.md)** | Connect Discord, Telegram, DingTalk, Feishu, iMessage, QQ | 5 min |
| 3 | **[Provider Configuration](guides/providers.md)** | OpenAI, Anthropic, Groq, Ollama, local models | 3 min |
| 4 | **[Skills Guide](guides/skills.md)** | Enable built-ins, create custom skills, publish | 5 min |
| 5 | **[MCP Server Setup](guides/mcp-setup.md)** | Connect filesystem, GitHub, Postgres, custom tools | 3 min |
| 6 | **[Cron Jobs & Automation](guides/cron-jobs.md)** | Schedule agent tasks, heartbeat, examples | 5 min |
| 7 | **[Monitoring](guides/monitoring.md)** | Watch websites and APIs for changes | 3 min |
| 8 | **[Marketplace](guides/marketplace.md)** | Browse, install, publish, credits | 5 min |
| 9 | **[Deployment](guides/deployment.md)** | Docker, fly.io, systemd, nginx | 10 min |
| 10 | **[ACP / IDE Integration](guides/acp-ide-integration.md)** | VS Code, Zed, JetBrains via ACP stdio | 3 min |
| 11 | **[Memory System](guides/memory-system.md)** | Auto-compaction, persistence, export | 3 min |
| 12 | **[CLI Reference](guides/cli-reference.md)** | Every command, every flag | reference |
| 13 | **[Set Up War Room](../INSTALL.md)** | Multi-agent coordination with ProwlrHub | 5 min |
| 14 | **[Cross-Network Setup](guides/cross-network-setup.md)** | Connect agents on different networks | 10 min |
| 15 | **[Configure Swarm](../README.swarm.md)** | Cross-machine command execution via Redis | 15 min |

---

## Architecture

Deep technical documentation for contributors and power users.

| Document | What's Inside |
|:---------|:-------------|
| **[CLAUDE.md](../CLAUDE.md)** | Full source layout, build commands, conventions, how every subsystem works |
| **[Leapfrog Design](plans/2026-03-09-prowlrbot-leapfrog-design.md)** | 60+ feature specs, competitive analysis, 12-month roadmap, security audit |
| **[Implementation Plan](plans/2026-03-09-prowlrbot-implementation-plan.md)** | Phased build strategy with priorities and dependencies |
| **[Phase 1 Details](plans/2026-03-09-prowlrbot-phase1-implementation.md)** | First phase: provider detection, smart routing, monitoring engine |
| **[Rebrand Spec](plans/2026-03-09-prowlrbot-rebrand-and-enhancement-design.md)** | Legacy → ProwlrBot migration: every file, import, and config changed |

### Core Flow

```
User Input
    │
    ▼
Channel (Discord/Telegram/Console/...)
    │
    ▼
ChannelManager ──► Queue (4 workers per channel)
    │                     │
    ▼                     ▼
AgentRunner          Debounce (batches rapid messages)
    │
    ▼
ProwlrBotAgent (ReAct reasoning loop)
    │
    ├──► Tools (shell, file I/O, browser, screenshot)
    ├──► Skills (PDF, DOCX, news, cron, email)
    ├──► MCP Clients (any MCP server, hot-reload)
    ├──► Memory (auto-compaction, token budget)
    │
    ▼
Smart Router
    │
    ├──► Score = w_cost × cost + w_perf × perf + w_avail × avail
    ├──► Try primary provider
    ├──► Fallback chain on failure
    │
    ▼
Response ──► Channel Output + Memory Persistence
```

### Provider Detection

```
App Startup
    │
    ▼
ProviderDetector ──► Scans env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
    │
    ▼
HealthChecker ──► Async probes to each detected provider
    │
    ▼
SmartRouter ──► Scores and ranks available providers
    │
    ▼
FallbackChain ──► If primary fails, try next in ranking
```

### Key Directories

```
~/.prowlrbot/              ← Working directory
├── config.json            ← Main configuration
├── chats/                 ← Chat history
├── active_skills/         ← Enabled skill packs
└── custom_channels/       ← Your custom channels

~/.prowlrbot.secret/       ← Secrets (mode 0o600)
└── envs.json              ← Encrypted API keys
```

---

## ROAR Protocol

ProwlrBot's agent communication protocol — 5 layers, full specification.

```
Layer 5: Stream    ──► Real-time event streaming (8 event types)
Layer 4: Exchange  ──► Unified message format (ROARMessage)
Layer 3: Connect   ──► Transport negotiation (stdio/HTTP/WS/gRPC)
Layer 2: Discovery ──► Agent directory + capability search
Layer 1: Identity  ──► W3C DID-based agent identity
```

| Layer | Spec | Summary |
|:------|:-----|:--------|
| Overview | **[ROAR-SPEC.md](protocols/ROAR-SPEC.md)** | Architecture overview, design principles, all 5 layers |
| 1. Identity | **[ROAR-IDENTITY.md](protocols/ROAR-IDENTITY.md)** | AgentCard, DID format, key management |
| 2. Discovery | **[ROAR-DISCOVERY.md](protocols/ROAR-DISCOVERY.md)** | AgentDirectory, capability search, federation |
| 3. Connect | **[ROAR-CONNECT.md](protocols/ROAR-CONNECT.md)** | Transport types, session lifecycle, reconnection |
| 4. Exchange | **[ROAR-EXCHANGE.md](protocols/ROAR-EXCHANGE.md)** | Message format, 7 intent types, signing |
| 5. Stream | **[ROAR-STREAM.md](protocols/ROAR-STREAM.md)** | StreamEvent, backpressure, subscriptions |

> **External spec:** [github.com/prowlrbot/roar-protocol](https://github.com/ProwlrBot/roar-protocol)

---

## War Room (ProwlrHub)

Multi-agent coordination system. Full documentation:

| Resource | What It Covers |
|:---------|:---------------|
| **[INSTALL.md](../INSTALL.md)** | Agent-executable setup (clone → 3 questions → connected) |
| **[Hub Architecture](../src/prowlrbot/hub/README.md)** | Database schema, bridge API, developer guide |
| **[War Room Protocol](../plugins/prowlr-hub/skills/war-room-protocol/SKILL.md)** | 7 Iron Rules for agent behavior |
| **[Coordinator Agent](../plugins/prowlr-hub/agents/war-room-coordinator.md)** | Task planning, conflict resolution, workload balancing |
| **[Cross-Network Guide](guides/cross-network-setup.md)** | Tailscale, Cloudflare, ngrok, SSH, ZeroTier |
| **[Network Connectivity](guides/cross-network-connectivity.md)** | Troubleshooting, optimization, WSL2 quirks |

### Slash Commands

| Command | What It Does |
|:--------|:-------------|
| `/board` | Display the mission board with all tasks |
| `/claim` | Create a task + lock files + start working |
| `/team` | See connected agents and their capabilities |
| `/broadcast` | Send a message to all agents |
| `/warroom` | Full dashboard: board + team + findings + events |

---

## Swarm (Cross-Machine Execution)

Run commands on remote machines via Redis + Tailscale:

| Resource | What It Covers |
|:---------|:---------------|
| **[Swarm Overview](../README.swarm.md)** | Architecture, quick start, CLI commands, Python API |
| **[Swarm Internals](../swarm/README.md)** | Project structure, adding capabilities, testing |

### How Swarm Differs From ProwlrHub

| | ProwlrHub (War Room) | Swarm (Execution) |
|:--|:---------------------|:-------------------|
| **Purpose** | Coordination | Remote execution |
| **Think of it as** | Shared whiteboard | Remote hands |
| **Transport** | SQLite + HTTP | Redis + Tailscale |
| **Tools** | claim, lock, share | shell, file, browser |
| **Use when** | Multiple agents, same project | Need Mac capabilities from WSL |

---

## Blog

Humanized posts about what we're building, why it matters, and where we're headed.

| Post | Tags | Summary |
|:-----|:-----|:--------|
| **[Introducing ProwlrBot](blog/2026-03-10-introducing-prowlrbot.md)** | launch, vision | Origin story — what we are and why we exist |
| **[War Room Is Live](blog/2026-03-10-war-room-is-live.md)** | launch, update | Multi-agent coordination ships today |
| **[Setting Up Your First Swarm](blog/2026-03-10-setting-up-your-first-swarm.md)** | guide | Step-by-step: 3 agents, named roles, zero conflicts |
| **[Security First, Always](blog/2026-03-10-security-first.md)** | deep-dive, alert | 26 vulns found and fixed — our security philosophy |
| **[What's Coming Next](blog/2026-03-10-whats-coming-next.md)** | vision, update | Protocols, marketplace, AgentVerse, 12-month roadmap |

---

## Research

| Document | What's Inside |
|:---------|:-------------|
| **[Agent Protocol Landscape](research/2026-03-10-agent-protocol-landscape.md)** | Competitive analysis of MCP, ACP, A2A, and agent platforms |
| **[ROAR Design Rationale](plans/2026-03-10-roar-protocol-design.md)** | Why we built ROAR, design decisions, trade-offs |

---

## Security & Contributing

| Document | What's Inside |
|:---------|:-------------|
| **[SECURITY.md](../SECURITY.md)** | Trust model, vulnerability reporting, security boundaries |
| **[CONTRIBUTING.md](../CONTRIBUTING.md)** | Commit conventions, PR process, skill structure, how to add channels/providers |
| **[DISCREPANCIES.md](DISCREPANCIES.md)** | CLAUDE.md accuracy audit — additions and corrections found in code |

---

## Quick Reference

### CLI Commands

```bash
prowlr app                          # Start the server
prowlr init --defaults              # Initialize config
prowlr chat "message"               # CLI chat
prowlr env set KEY value            # Set secret
prowlr env list                     # List secrets
prowlr channels add <type>          # Add channel
prowlr channels list                # List channels
prowlr skills list                  # List skills
prowlr skills enable <name>         # Enable skill
prowlr monitor add <url>            # Add monitor
prowlr monitor list                 # List monitors
prowlr cron add "task" --schedule   # Add cron job
prowlr swarm status                 # Swarm status
prowlr swarm enqueue <capability>   # Queue swarm job
```

### Config Locations

| Path | Contains |
|:-----|:---------|
| `~/.prowlrbot/config.json` | Main configuration |
| `~/.prowlrbot/chats/` | Chat history |
| `~/.prowlrbot/active_skills/` | Enabled skills |
| `~/.prowlrbot/custom_channels/` | Custom channel adapters |
| `~/.prowlrbot.secret/envs.json` | Encrypted API keys |

### API Endpoints

```
GET    /api/version        Server version
GET    /api/agents         List agents
POST   /api/agents         Create agent
GET    /api/agents/{id}    Get agent
PUT    /api/agents/{id}    Update agent
DELETE /api/agents/{id}    Delete agent
GET    /api/channels       List channels
POST   /api/channels       Add channel
GET    /api/skills         List skills
GET    /api/cron           List cron jobs
POST   /api/cron           Add cron job
GET    /api/providers      Available providers
GET    /api/config         Current config
PUT    /api/config         Update config
WS     /ws/dashboard       Real-time events
```

---

<p align="center">
  Can't find what you need? <a href="https://github.com/prowlrbot/prowlrbot/issues">Open an issue</a> — we respond fast.
</p>
