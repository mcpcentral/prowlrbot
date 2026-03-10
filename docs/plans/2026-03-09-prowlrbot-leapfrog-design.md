# ProwlrBot: Leapfrog Design — The Open-Source Agent Platform That Wins

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Date**: 2026-03-09
**Status**: Draft — Awaiting Approval
**Vision**: The most customizable, transparent, multi-channel autonomous AI agent platform.
**Tagline**: "Always watching. Always ready."

---

## Executive Summary

ProwlrBot leapfrogs every major AI agent platform by combining the best of each into one open-source, self-hosted, customizable platform:

| We Take From | What We Take | How We Make It Better |
|-------------|-------------|----------------------|
| **Manus.ai** | Split-panel UI, live workspace, session replay | Open-source, self-hosted, customizable panels |
| **Superset** | Parallel agent orchestration, worktree isolation, diff viewer | Not just CLI agents — deep agent integration + orchestration |
| **Opcode** | Timeline/checkpoints, usage analytics, agent library | Multi-channel (7 platforms), not just code |
| **Devin** | Parallel agents, auto-documentation (Wiki) | Free tier, open-source, community skills |
| **OpenAI Operator** | Graduated autonomy (Watch/Guide/Delegate/Auto) | Works with ANY model, not just GPT |
| **Claude Code** | MCP protocol, multi-agent spawning | Add ACP + A2A for full protocol coverage |
| **OpenClaw** | ACP protocol, messaging-first, massive community | Better UI, monitoring engine, swarm dashboard |
| **Replit** | Zero-to-value speed, mobile companion | Self-hosted + cloud options |
| **LangGraph** | Agent observability, traces, replay debugging | Built-in, not separate tool |
| **CrewAI** | Role-based agent teams | Visual team builder in dashboard |

**Core Differentiators Nobody Else Has Combined:**
1. 7+ communication channels (Discord, Telegram, DingTalk, Feishu, QQ, iMessage, Console)
2. Web monitoring engine ("Always watching")
3. Docker swarm with macOS bridge for multi-device coordination
4. MCP + ACP + A2A — first platform to support all three agent protocols
5. 3 local model backends (llama.cpp, MLX, Ollama)
6. Skills marketplace with community contributions
7. Fully open-source and self-hosted

---

## Part 1: Hybrid Dashboard Design (Adaptive + Mission Control + Manus Workspace)

### Design Philosophy

**Adaptive by default. Powerful on demand.**

- New users see a clean, simple interface — chat + monitoring alerts
- As complexity grows, panels slide in automatically
- Power users customize their layout (drag, resize, pin panels)
- Every panel is optional, closeable, and rememberable

### Layout Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Header Bar: ProwlrBot | Status Indicator | Notifications Bell  │
│  [Autonomy Slider: Watch ←→ Guide ←→ Delegate ←→ Autonomous]   │
├────────┬─────────────────────────────────────────────────────────┤
│        │                                                         │
│  Side  │              Main Workspace Area                        │
│  bar   │     ┌─────────────────┬─────────────────────┐          │
│        │     │                 │                       │          │
│ Tabs:  │     │   Chat Panel    │  Live Workspace      │          │
│ - Home │     │   (always on)   │  (adaptive)          │          │
│ - Agent│     │                 │  - Browser view       │          │
│ - Swarm│     │  [Input box]    │  - Terminal output    │          │
│ - Mon. │     │  [File attach]  │  - Code diff          │          │
│ - Tasks│     │  [Voice input]  │  - File changes       │          │
│ - Sett.│     │                 │  - Monitor alerts     │          │
│        │     ├─────────────────┴─────────────────────┤          │
│        │     │  Activity Feed (collapsible bottom)    │          │
│        │     │  Tool calls | MCP | Memory | Reasoning │          │
│        │     └───────────────────────────────────────┘          │
├────────┴─────────────────────────────────────────────────────────┤
│  Status Bar: Model | Tokens Used | Cost | Latency | Connected   │
└──────────────────────────────────────────────────────────────────┘
```

### Panel System

Each panel is a draggable, resizable, closeable widget:

| Panel | Purpose | Appears When |
|-------|---------|-------------|
| **Chat** | Primary interaction | Always visible |
| **Live Workspace** | Agent's active view (browser, terminal, code) | Agent starts complex task |
| **Activity Feed** | Real-time tool calls, MCP interactions, reasoning | User enables or agent is working |
| **Task Board** | Kanban of agent sub-tasks (pending → running → done) | Agent decomposes a goal |
| **Timeline** | Session checkpoints with branching (from Opcode) | User or auto-checkpoint triggers |
| **Diff Viewer** | Side-by-side code/file changes (from Superset) | Agent modifies files |
| **Swarm Dashboard** | Worker status, job queue, bridge capabilities | Swarm is active |
| **Monitor Alerts** | Web change detection alerts, uptime status | Monitors are configured |
| **Usage Analytics** | Cost, tokens, model usage over time | Always available in settings |
| **Agent Teams** | Visual multi-agent orchestration (from CrewAI) | Multi-agent task |

### Graduated Autonomy Control

A slider in the header controls how much the agent does on its own:

| Level | Behavior | UI Effect |
|-------|----------|-----------|
| **Watch** | Agent explains what it WOULD do, waits for approval on every step | Every action shows "Allow?" prompt |
| **Guide** | Agent acts on routine tasks, asks for approval on consequential ones | Only significant actions prompt |
| **Delegate** | Agent acts freely, notifies on completion and errors | Notifications only |
| **Autonomous** | Full autopilot, agent handles everything including error recovery | Minimal interruption |

Users set a default level AND per-task overrides. The agent can request escalation ("I'm about to delete a file — should I switch to Guide mode?").

### Real-Time Communication (WebSocket Upgrade)

Current: HTTP polling for push messages (60s window, 500 max).
New: WebSocket connection for live streaming.

```
Client ←──WebSocket──→ Server
  │                      │
  │  event: tool_call    │  Agent calls a tool
  │  event: mcp_request  │  MCP server interaction
  │  event: reasoning    │  Agent's thinking (optional)
  │  event: task_update  │  Sub-task status change
  │  event: monitor_alert│  Web change detected
  │  event: swarm_job    │  Swarm job status change
  │  event: checkpoint   │  Auto-checkpoint created
  │  event: stream_token │  Response token streaming
```

### Session Replay & Timeline

Inspired by Opcode and Manus:

- Every session auto-records: messages, tool calls, file changes, reasoning
- Timeline scrubber shows chronological agent activity
- Checkpoints: auto-created at key moments (task completion, error recovery, user intervention)
- Branching: fork from any checkpoint to explore alternatives
- Export: download session as JSON or share as read-only replay link

---

## Part 2: Agent IDE / Editor

Inspired by Opcode (single-agent depth) and Superset (multi-agent orchestration):

### Per-Agent Customization (Every Agent is Unique)

Each agent is a fully customizable entity with its own identity, soul, memory, tools, and avatar:

```yaml
agent:
  # Identity & Avatar
  name: "Prowlr Research Agent"
  avatar:
    base: "owl"                # cat, dog, fox, owl, robot, dragon, custom
    color: "#6B5CE7"
    accessories: ["glasses", "notebook"]
    mood: "focused"            # Auto-derived from recent activity
    level: 8                   # XP from completed tasks
    reputation: 4.7            # Community rating

  # Soul (Personality & Behavior)
  soul:
    personality: "Analytical, thorough, asks clarifying questions"
    tone: "Professional but approachable"
    soul_file: "SOUL.md"       # Full personality document
    profile_file: "PROFILE.md" # Background and knowledge areas
    agents_file: "AGENTS.md"   # Behavioral instructions

  # Memory (Per-Agent Knowledge)
  memory:
    type: "persistent"         # persistent, session-only, shared
    max_tokens: 50000          # Budget before compaction
    compaction_strategy: "summarize"  # summarize, prune, archive
    shared_with: []            # Agent IDs that share this memory pool
    knowledge_bases: ["research_kb"]  # Marketplace knowledge bases

  # Tools (What the Agent Can Do)
  tools:
    enabled: [shell, file_io, browser, memory_search, send_file]
    disabled: [desktop_screenshot]
    custom_tools: []           # Marketplace tools
    permissions:
      shell:
        allowed_commands: ["grep", "find", "curl", "python"]
        blocked_commands: ["rm", "dd", "mkfs"]
      file_io:
        allowed_paths: ["/workspace", "/tmp"]
        blocked_paths: ["~/.prowlrbot.secret"]

  # Skills
  skills:
    builtin: ["file_reader", "news", "pdf"]
    marketplace: ["seo_analyzer", "newsletter_writer"]
    custom: ["my_custom_skill"]

  # Model & Inference
  model:
    preferred: "claude-opus-4-6"
    fallback_chain: ["claude-sonnet-4-6", "groq-llama-4", "ollama-local"]
    temperature: 0.7
    max_tokens: 4096

  # Autonomy
  autonomy:
    default_level: "delegate"  # watch, guide, delegate, autonomous
    escalation_triggers: ["file deletion", "external API calls", "spending over $1"]
    auto_checkpoint: true

  # Channels
  channels: [discord, telegram, console]

  # AgentVerse Presence
  agentverse:
    visible: true
    home_zone: "workshop"
    guild: "research_guild"
    trading_enabled: true
    battle_enabled: true
```

### Agent Editor Features

| Feature | Description | Inspiration |
|---------|-------------|-------------|
| **Agent Creator** | Visual form with ALL customization fields above | Opcode CC Agents |
| **Agent Library** | Browse, search, import community agents from marketplace | Opcode Agent Library |
| **Agent Teams Builder** | Visual drag-and-drop team composition (director + specialists) | CrewAI, OpenClaw Agent Teams |
| **Soul Editor** | Edit SOUL.md, PROFILE.md, AGENTS.md with live preview + personality test chat | Opcode CLAUDE.md Editor |
| **Memory Manager** | View, search, edit, prune memories; visualize as knowledge graph | New — unique to ProwlrBot |
| **Tool Configurator** | Enable/disable tools, set per-tool permissions, command allowlists | Security-first approach |
| **Skills Editor** | Create/edit SKILL.md with YAML frontmatter, test in sandbox | Existing ProwlrBot skills system |
| **MCP Manager** | Visual MCP server config, connection testing, capability browser | Existing + Opcode MCP Manager |
| **Avatar Designer** | Visual avatar customization with live preview | AgentVerse integration |
| **Workspace Manager** | File browser, Monaco editor, zip export/import | Existing ProwlrBot workspace |
| **Worktree Isolation** | Each agent task gets its own git worktree | Superset |

### Interactive UI for ALL Users (Power Users + Beginners)

Two modes, same dashboard:

| Mode | Target | Experience |
|------|--------|-----------|
| **Easy Mode** | Beginners | Wizard-driven setup, pre-built templates, guided tours, "Ask me anything" chat |
| **Pro Mode** | Power users | Full panel system, JSON config editors, terminal access, custom agent code |

Users toggle between modes. Easy Mode hides complexity but doesn't remove it — Pro Mode reveals everything underneath.

**Beginner Flow:**
```
Welcome → Pick a template ("Social Media Bot", "Research Assistant", "Monitor")
→ Connect channels (one-click OAuth) → Customize personality → Deploy
```

**Power User Flow:**
```
Dashboard → Create agent (custom prompt, tools, skills, model)
→ Configure worktree isolation → Set autonomy level → Wire into team → Deploy
```

### Visual Agent Graph (See ALL Agents + Sub-agents)

A live, interactive graph visualization showing every running agent:

```
┌─────────────────────────────────────────────┐
│           Visual Agent Graph                │
│                                             │
│    ┌──────────┐                             │
│    │ Director │ ← You're here (main agent)  │
│    │  Agent   │                             │
│    └────┬─────┘                             │
│         │                                   │
│    ┌────┼────────────┐                      │
│    ▼    ▼            ▼                      │
│  ┌────┐ ┌────┐  ┌────────┐                 │
│  │Sub │ │Sub │  │ Swarm  │                  │
│  │ A  │ │ B  │  │Worker 1│                  │
│  │🟢  │ │🟡  │  │🟢     │                  │
│  └────┘ └────┘  └────────┘                  │
│                                             │
│  🟢 Running  🟡 Waiting  🔴 Error  ⚪ Idle  │
└─────────────────────────────────────────────┘
```

- Click any agent node to see its: current task, reasoning, tool calls, memory, cost
- Drag to rearrange the graph
- Right-click to: pause, resume, redirect, kill, fork
- Sub-agents appear as children of their parent
- Swarm workers shown with device/container labels
- Real-time status updates via WebSocket

### Swarm Personality & Customization

Each swarm worker gets its own personality, fallback chain, and behavior config:

```python
class SwarmWorkerConfig:
    """Configuration for an individual swarm worker."""
    name: str                    # "Research Specialist", "Code Writer", etc.
    personality: str             # System prompt / personality file
    model_preference: str        # Preferred model (e.g., "claude-opus-4-6")
    fallback_models: list[str]   # Fallback chain if preferred unavailable
    autonomy_level: str          # watch/guide/delegate/autonomous
    capabilities: list[str]      # What this worker can do
    max_concurrent_tasks: int    # Parallel task limit
    custom_tools: list[str]      # Additional tools beyond defaults
    custom_skills: list[str]     # Skills this worker has access to
    tags: dict                   # Custom metadata for routing
```

**Swarm Dashboard Features:**
- Visual topology of all workers (which device, which container, what capabilities)
- Per-worker personality editor (name, avatar, system prompt)
- Drag-and-drop capability assignment
- Fallback chain builder (if Worker A fails → try Worker B → try Worker C)
- Real-time cost tracking per worker
- One-click scale up/down (spin new workers or shut down idle ones)

### Revenue-Sharing Community Marketplace

Not just a skills store — a **revenue-sharing ecosystem**:

```
┌──────────────────────────────────────────────┐
│         ProwlrBot Marketplace                │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │  Skills   │ │  Agents  │ │  Templates   │ │
│  │  Store    │ │  Store   │ │  Store       │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │  MCP     │ │  Channel │ │  Workflows   │ │
│  │  Servers │ │  Plugins │ │  (Pipelines) │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│                                              │
│  Revenue Split: 70% Creator / 30% Platform   │
└──────────────────────────────────────────────┘
```

**What community members can sell/share:**

| Category | Description | Examples |
|----------|-------------|---------|
| **Skills** | Custom SKILL.md bundles with scripts | SEO analyzer, PDF summarizer, email drafter |
| **Agent Templates** | Pre-configured agents (personality + tools + skills) | "Marketing Director", "DevOps Monitor", "Research Analyst" |
| **System Prompts** | Battle-tested system prompts for specific use cases | Customer support tone, technical writer, creative storyteller |
| **Prompt Specs** | Structured prompt libraries with variables and chains | Interview question generator, code review checklist, report template |
| **MCP Server Configs** | Plug-and-play MCP server setups | GitHub MCP, Slack MCP, database MCP, custom API wrappers |
| **Channel Plugins** | Custom channel integrations | WhatsApp, Slack, LINE, custom webhook channels |
| **Workflows** | Multi-step automation pipelines (visual or YAML) | "PR Review Pipeline", "Daily Digest", "Social Media Calendar" |
| **Knowledge Bases** | Curated datasets, RAG collections, domain knowledge | Industry-specific knowledge, company wikis, research collections |
| **Benchmark Suites** | Custom test suites for model evaluation | Domain-specific benchmarks, regression test packs |
| **AgentVerse Assets** | Avatar skins, accessories, home decorations, themes | Character designs, badge sets, seasonal cosmetics |
| **Dashboard Themes** | Custom dashboard layouts, color schemes, panel configs | "Hacker Terminal", "Minimal Light", "Cyberpunk" |
| **Team Configs** | Pre-built agent team compositions with coordination rules | "Startup Team", "Content Factory", "Research Lab" |

**Revenue Model:**
- Free tier: unlimited free listings, community ratings, basic analytics
- Paid listings: 70/30 split (creator gets 70%)
- Subscription bundles: curated packs for verticals (marketing, dev, research)
- Enterprise licensing: white-label marketplace for teams
- AgentVerse cosmetics: premium avatar items and zone access
- Featured listings: pay to promote in marketplace (like app store ads)

**Team Agent / Real-Life Sim Concept:**

A "Team Agent" mode where users build virtual teams of AI agents that simulate real organizational dynamics:

```yaml
team: "Marketing Department"
agents:
  - name: "Content Lead"
    role: director
    personality: "Strategic thinker, data-driven, focuses on ROI"
    delegates_to: [copywriter, designer, analyst]
  - name: "Copywriter"
    role: specialist
    personality: "Creative, witty, knows brand voice"
    skills: [social_media, blog_writing, email]
  - name: "Data Analyst"
    role: specialist
    personality: "Numbers-focused, finds insights in data"
    skills: [analytics, reporting, competitor_monitoring]
  - name: "Community Manager"
    role: specialist
    personality: "Empathetic, responsive, community-first"
    skills: [discord_management, support, engagement]
coordination: round_robin  # or: hierarchical, consensus, auction
fallback: escalate_to_human
```

Users can:
- Watch agents collaborate in real-time (chat between agents visible)
- Intervene at any point (jump in, redirect, override)
- Save team configurations as marketplace templates
- Share team performance metrics

### Agent-Agnostic Execution (Superset Pattern)

ProwlrBot agents are deeply integrated, but we ALSO support external CLI agents:

```python
# prowlrbot can orchestrate any CLI agent
class ExternalAgentRunner:
    """Run any CLI agent (Claude Code, Codex, etc.) as a ProwlrBot worker."""
    agent_command: str  # e.g., "claude-code", "codex"
    worktree_path: str  # isolated git worktree
    status: AgentStatus  # running, waiting, completed, error
```

This means ProwlrBot can be BOTH:
- A standalone agent platform (its own agents)
- An orchestration layer for other agents (like Superset)

---

## Part 3: ROAR Protocol — Real-time Open Agent Runtime

### The Problem with Current Protocols

Right now, agent communication is fragmented:
- **MCP** handles tools, but not agent-to-agent
- **A2A** handles agent-to-agent, but not tools or IDEs
- **ACP** handles IDEs, but not agent-to-agent or tools
- **ANP** handles discovery, but not execution

Developers need 4 different protocols to build a complete agent system. That's like needing HTTP for web pages, a different protocol for APIs, another for WebSockets, and another for service discovery — all separate.

**ROAR unifies them.**

### What is ROAR?

**ROAR (Real-time Open Agent Runtime)** is a unified protocol that combines tool integration, agent-to-agent communication, IDE bridging, and decentralized discovery into a single spec.

```
┌─────────────────────────────────────────────────────────┐
│                    ROAR Protocol                         │
│         Real-time Open Agent Runtime                     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 1: ROAR/Identity                           │   │
│  │  W3C DID-based agent identity                     │   │
│  │  Portable, cryptographically owned                │   │
│  │  Agent Cards with capabilities + permissions      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 2: ROAR/Discovery                          │   │
│  │  Decentralized agent discovery (no central reg.)  │   │
│  │  DNS-like resolution for agent endpoints          │   │
│  │  Hub federation for social/marketplace            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 3: ROAR/Connect                            │   │
│  │  Unified transport: stdio, HTTP, WebSocket, gRPC  │   │
│  │  Auto-negotiation of best transport               │   │
│  │  Encryption (TLS) and auth (HMAC/JWT) built-in    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 4: ROAR/Exchange                           │   │
│  │  Unified message format for ALL interactions:     │   │
│  │  • Agent ↔ Tool (replaces MCP)                    │   │
│  │  • Agent ↔ Agent (replaces A2A)                   │   │
│  │  • Agent ↔ IDE (replaces ACP)                     │   │
│  │  • Agent ↔ Human (chat, voice, visual)            │   │
│  │  Task lifecycle: create → assign → execute → done │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Layer 5: ROAR/Stream                             │   │
│  │  Real-time event streaming                        │   │
│  │  Live activity feeds, world state updates         │   │
│  │  Session replay, checkpoint sync                  │   │
│  │  AgentVerse world events                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### How ROAR Compares

| Feature | MCP | A2A | ACP | ANP | **ROAR** |
|---------|-----|-----|-----|-----|----------|
| Tool integration | Yes | No | No | No | **Yes** |
| Agent-to-agent | No | Yes | No | No | **Yes** |
| IDE bridging | No | No | Yes | No | **Yes** |
| Discovery | No | Partial | No | Yes | **Yes** |
| Identity (DID) | No | Partial | No | Yes | **Yes** |
| Real-time streaming | No | No | No | No | **Yes** |
| Unified transport | stdio | HTTP | stdio | HTTP | **stdio + HTTP + WS + gRPC** |
| Built-in auth | No | No | No | No | **Yes (HMAC + JWT + mTLS)** |
| Backward compatible | — | — | — | — | **Yes (speaks MCP, A2A, ACP)** |

### ROAR is Backward Compatible

ROAR doesn't replace existing protocols — it wraps them:

```
External MCP Server → ROAR/Connect adapter → ProwlrBot understands it
External A2A Agent  → ROAR/Connect adapter → ProwlrBot understands it
External ACP IDE    → ROAR/Connect adapter → ProwlrBot understands it
```

Any agent that speaks MCP, A2A, or ACP can talk to ROAR. But ROAR agents get the full unified experience.

### ROAR Message Format

```json
{
  "roar": "1.0",
  "id": "msg_a1b2c3",
  "from": {
    "did": "did:roar:agent:research-owl-7f3a",
    "type": "agent",
    "capabilities": ["research", "analysis"]
  },
  "to": {
    "did": "did:roar:tool:web-browser",
    "type": "tool"
  },
  "intent": "execute",
  "payload": {
    "action": "navigate",
    "params": {"url": "https://example.com"}
  },
  "context": {
    "session_id": "sess_xyz",
    "task_id": "task_123",
    "autonomy_level": "delegate",
    "parent_message": "msg_prev"
  },
  "auth": {
    "signature": "hmac-sha256:...",
    "timestamp": 1741536000
  }
}
```

One message format for EVERYTHING:
- Agent → Tool: `intent: "execute"`, `to.type: "tool"`
- Agent → Agent: `intent: "delegate"`, `to.type: "agent"`
- Agent → IDE: `intent: "update"`, `to.type: "ide"`
- Agent → Human: `intent: "ask"`, `to.type: "human"`

### Why This Makes ProwlrBot Look Like Google

| What Google Did | What We Do |
|----------------|-----------|
| Created A2A (agent-to-agent) | Created ROAR (unified everything) |
| A2A is one layer | ROAR is 5 layers, covers the full stack |
| A2A is HTTP-only | ROAR auto-negotiates transport |
| A2A launched under Linux Foundation | ROAR launches as open spec on GitHub |
| A2A has 100+ supporters | ROAR has backward compat with ALL of them |

### ROAR Spec Deliverables

```
docs/roar-protocol/
├── README.md                    # Protocol overview
├── spec/
│   ├── 01-identity.md           # ROAR/Identity (W3C DID-based)
│   ├── 02-discovery.md          # ROAR/Discovery (decentralized)
│   ├── 03-connect.md            # ROAR/Connect (transport negotiation)
│   ├── 04-exchange.md           # ROAR/Exchange (unified messages)
│   └── 05-stream.md             # ROAR/Stream (real-time events)
├── sdks/
│   ├── python/                  # pip install roar-protocol
│   └── typescript/              # npm install @roar/sdk
├── adapters/
│   ├── mcp-adapter.py           # Speak MCP via ROAR
│   ├── a2a-adapter.py           # Speak A2A via ROAR
│   └── acp-adapter.py           # Speak ACP via ROAR
└── examples/
    ├── agent-to-tool.py
    ├── agent-to-agent.py
    └── agent-to-ide.py
```

---

## Part 3b: Protocol Integration (MCP + ACP + A2A via ROAR)

### Current State
- MCP: Already implemented (tool integration)

### New: ACP (Agent Client Protocol)

ProwlrBot exposes itself as an ACP-compatible agent:

```
IDE (VS Code, Zed, JetBrains)
    ↓ JSON-RPC 2.0 over stdio
ProwlrBot ACP Server
    ↓
    initialize → session/new → session/prompt → stream response
```

**Implementation:**
- `pip install agent-client-protocol`
- New module: `src/prowlrbot/protocols/acp_server.py`
- CLI command: `prowlr acp` (expose as ACP agent over stdio)
- Any IDE with ACP support can use ProwlrBot as its coding agent

### New: A2A (Agent2Agent Protocol)

ProwlrBot agents discover and coordinate with other A2A-compatible agents:

```
ProwlrBot Agent A ←──A2A (HTTP/JSON-RPC)──→ External Agent B
    │                                            │
    ├── Agent Card (capability discovery)        │
    ├── Task lifecycle (create/update/complete)   │
    └── Context sharing (files, state)           │
```

**Implementation:**
- New module: `src/prowlrbot/protocols/a2a_server.py`
- Agent Cards: JSON capability descriptors for ProwlrBot agents
- Task management: REST endpoints for cross-agent task delegation
- Integration with swarm: A2A replaces custom Redis protocol for inter-agent communication

### Protocol Stack

```
┌─────────────────────────────────────┐
│          ProwlrBot Agent            │
├─────────┬──────────┬────────────────┤
│   MCP   │   ACP    │     A2A       │
│ (Tools) │ (IDEs)   │  (Agents)     │
│         │          │               │
│ Connect │ Expose   │ Discover &    │
│ to any  │ to any   │ coordinate    │
│ tool    │ editor   │ with any      │
│         │          │ agent         │
└─────────┴──────────┴────────────────┘
```

---

## Part 4: Marketing Agent

A built-in ProwlrBot skill that handles marketing automation:

### Marketing Agent Architecture

```python
class MarketingAgent:
    """Autonomous marketing agent for ProwlrBot projects."""

    capabilities = [
        "social_media_posting",    # X/Twitter, Reddit, HackerNews
        "content_generation",      # Blog posts, changelogs, tutorials
        "community_monitoring",    # Track mentions, sentiment, feedback
        "seo_optimization",        # Meta tags, descriptions, keywords
        "analytics_tracking",      # GitHub stars, npm downloads, traffic
        "competitor_monitoring",   # Track competitor releases/features
        "release_announcements",   # Auto-generate release notes + post
    ]
```

### Marketing Skill (SKILL.md)

```yaml
name: marketing
description: Autonomous marketing agent for open-source projects
triggers:
  - git tag (auto-generate release announcement)
  - weekly (generate engagement report)
  - monitor alert (competitor released a feature)
```

### Growth Playbook (Built into the Agent)

The marketing agent follows proven strategies from successful projects:

1. **Content Pipeline**: Commit → Changelog → Blog post → Social media → Community
2. **Engagement Loops**: GitHub star → Discord invite → First contribution → Ambassador
3. **Competitive Intel**: Monitor competitor repos, releases, pricing changes
4. **SEO Strategy**: Auto-generate meta descriptions, structured data, sitemap

### Marketing Skill File Structure

```
skills/marketing/
  SKILL.md              # Manifest: name, description, triggers
  references/
    brand_voice.md      # Tone, messaging guidelines, tagline usage
    platforms.md        # Platform-specific formatting (X 280 chars, Reddit markdown, HN plain text)
    competitors.md      # Tracked competitor repos and keywords
  scripts/
    monitor_mentions.py # Track @mentions on Twitter/X, Reddit, HN, GitHub
    draft_social_post.py# Generate platform-specific content
    track_metrics.py    # GitHub stars, Discord members, PyPI downloads
    weekly_digest.py    # Auto-generate weekly community update
    release_notes.py    # Generate changelog + announcement from git tags
```

### Cron-Powered Marketing Automation

Uses ProwlrBot's existing cron system:

| Schedule | Action | Output Channel |
|----------|--------|---------------|
| Daily 9am | Scan mentions, draft responses | Discord #marketing-agent |
| Monday 10am | Weekly Wins digest with metrics | Twitter/X, Discord, Blog |
| On git tag | Auto-draft release announcement | All channels |
| Daily 6pm | Competitor activity report | Discord #intel |
| Friday 3pm | "Skill of the Week" showcase | Twitter/X, Discord |

### Launch Playbook (Proven Tactics)

**Week 1-2: Foundation**
- Record 3 "wow" demo videos (30-90s): multi-channel management, cron automation, skill creation
- Revamp README: outcome-framing, GIF hero, one-command install
- Set up Discord with channels: #general, #showcase, #help, #contributors, #marketing-agent

**Week 3-4: Hacker News Launch**
- Post as "Show HN: ProwlrBot — Open-source AI agent across Discord, Telegram, DingTalk with cron jobs and monitoring"
- Tuesday-Thursday, 9-11 AM EST (optimal timing per research)
- Team ready to engage in comments within first 2 hours
- Target: 200-500 star burst

**Week 4-6: Reddit Push**
- r/selfhosted, r/LocalLLaMA, r/opensource, r/homelab
- Frame as "I built X to solve Y" tutorials, not product pitches
- Target posts: "How I set up an AI assistant that auto-digests RSS into Telegram"

**Week 6: Product Hunt**
- Use as credibility badge, not primary growth driver
- 2-minute demo video, clear screenshots, compelling tagline

**Week 6-10: Chinese Community Push**
- Zhihu, CSDN, Juejin, WeChat developer groups
- DingTalk/Feishu support is a unique advantage for Chinese market
- 2x addressable audience with dual-language content

### The Meta-Play

ProwlrBot markets ITSELF using its own marketing skill. This is triple-duty:
1. **Actual utility** — automates real marketing work
2. **Live demo** — "this tweet was posted by ProwlrBot via its cron skill"
3. **Dogfooding** — surfaces bugs and UX issues in production use

---

## Part 5: 12-Month Roadmap

### Q1: Foundation & First Viral Moment (Months 1-3)

**Goal:** 1,000 GitHub stars, 500 Discord members, 100 active users

| Week | Deliverable |
|------|------------|
| 1-2 | Polish `pip install prowlrbot && prowlr init --defaults` (< 60s to value) |
| 3-4 | WebSocket upgrade for real-time dashboard |
| 5-6 | Hybrid dashboard MVP (Chat + Activity Feed + Task Board) |
| 7-8 | Graduated autonomy controls (Watch/Guide/Delegate/Auto) |
| 9-10 | 90-second cinematic demo video |
| 11-12 | Product Hunt launch + HN technical deep-dive |

**Marketing Actions:**
- Discord server launch
- GitHub Discussions for architecture conversations
- CONTRIBUTING.md with 20+ "good first issue" labels
- Twitter/X build-in-public thread
- Submit to awesome-ai-agents lists

### Q2: Retention & Developer Experience (Months 4-6)

**Goal:** 5,000 GitHub stars, 2,000 Discord, 500 active users

| Week | Deliverable |
|------|------------|
| 13-14 | Skills Marketplace with community submissions |
| 15-16 | ACP protocol support (IDE integration) |
| 17-18 | Session replay with timeline scrubbing |
| 19-20 | Agent Editor (create custom agents visually) |
| 21-22 | Pre-built agent templates (5 categories) |
| 23-24 | First ProwlrBot Hackathon (virtual, 2 weeks) |

**Marketing Actions:**
- "Skill of the Week" showcase series
- Guest posts on dev.to, Medium, Hashnode
- Video tutorials: "Build Your First ProwlrBot Skill in 10 Minutes"
- Conference lightning talks

### Q3: Scale & Multi-Agent (Months 7-9)

**Goal:** 15,000 GitHub stars, 5,000 Discord, 2,000 active users

| Week | Deliverable |
|------|------------|
| 25-26 | A2A protocol support (agent-to-agent coordination) |
| 27-28 | Agent Teams Builder (visual multi-agent orchestration) |
| 29-30 | External agent support (run Claude Code, Codex as workers) |
| 31-32 | Swarm Dashboard with visual monitoring |
| 33-34 | ProwlrBot Cloud beta (hosted version, free tier) |
| 35-36 | Mobile companion app (iOS/Android) |

**Marketing Actions:**
- Second hackathon ($15K prizes)
- Ambassador program
- Enterprise pilot outreach (3-5 companies)
- Apply to Y Combinator or accelerators

### Q4: Enterprise & Ecosystem (Months 10-12)

**Goal:** 30,000 GitHub stars, 10,000 Discord, 5,000 active users, $50K MRR

| Week | Deliverable |
|------|------------|
| 37-38 | Visual workflow builder (drag-and-drop agent pipelines) |
| 39-40 | Enterprise features (SSO, audit logs, RBAC) |
| 41-42 | Model Leaderboard (live rankings, custom benchmarks) |
| 43-44 | Plugin SDK for third-party developers |
| 45-46 | Self-hosted enterprise package (K8s/Helm) |
| 47-48 | Annual "State of ProwlrBot" report + virtual summit |

**Pricing Model (Credit-Based Hybrid):**

| Tier | Price | Credits/Month | Features |
|------|-------|--------------|----------|
| Free (Self-Hosted) | $0 | Unlimited | Full platform, own infrastructure |
| Cloud Free | $0 | 100/day | Hosted, limited usage |
| Cloud Pro | $29/mo | 3,000 | Priority models, analytics |
| Cloud Team | $99/mo | 15,000 | Multi-user, shared agents |
| Enterprise | Custom | Custom | SSO, SLA, on-prem, support |

---

## Part 6: Technical Architecture for Dashboard

### Frontend Stack (Upgrade Path)

Current: React 18 + Vite + Ant Design + Less
Target: React 18 + Vite + Ant Design + Tailwind CSS + shadcn/ui components

**New packages needed:**
- `xterm.js` — Terminal emulation in browser (same as VS Code, Superset)
- `@monaco-editor/react` — Code editor + diff viewer
- `react-grid-layout` — Draggable, resizable panel system
- `recharts` — Usage analytics charts
- WebSocket client (native browser API)

### Backend Additions

```
src/prowlrbot/
├── protocols/
│   ├── __init__.py
│   ├── acp_server.py      # ACP JSON-RPC server over stdio
│   ├── a2a_server.py      # A2A REST endpoints + Agent Cards
│   └── websocket.py       # WebSocket event streaming
├── dashboard/
│   ├── __init__.py
│   ├── events.py           # Event types for real-time streaming
│   ├── timeline.py         # Session recording + checkpoints
│   ├── analytics.py        # Usage tracking (tokens, cost, latency)
│   └── agent_teams.py      # Multi-agent team orchestration
├── marketing/
│   ├── __init__.py
│   ├── agent.py            # Marketing automation agent
│   ├── social.py           # Social media posting
│   ├── analytics.py        # Growth metrics tracking
│   └── competitor.py       # Competitor monitoring
```

### WebSocket API Design

```python
# Server → Client events
class DashboardEvent:
    type: str          # "tool_call", "reasoning", "task_update", etc.
    timestamp: float
    session_id: str
    data: dict         # Event-specific payload

# Client → Server commands
class DashboardCommand:
    type: str          # "set_autonomy", "cancel_task", "fork_checkpoint", etc.
    data: dict
```

### Database Additions (SQLite)

```sql
-- Session timeline & checkpoints
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    label TEXT,
    state_snapshot JSON,
    parent_id TEXT,           -- For branching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent activity log
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- tool_call, mcp_request, reasoning, etc.
    event_data JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage analytics
CREATE TABLE usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent teams
CREATE TABLE agent_teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config JSON,              -- Team composition, roles, coordination mode
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Part 7: Competitive Moats

### Why ProwlrBot Wins

1. **Open-source + self-hosted**: No vendor lock-in. Full data control. Unlike Manus ($2B closed), Devin (enterprise-only), or Operator (ChatGPT-only).

2. **Multi-channel native**: 7 platforms from day one. No other agent platform works across Discord, Telegram, DingTalk, Feishu, QQ, iMessage, AND web console.

3. **Full protocol stack**: MCP + ACP + A2A = works with any tool, any editor, any agent. First platform to support all three.

4. **Monitoring engine**: "Always watching" is a unique value prop. No competitor combines autonomous agents WITH web monitoring/change detection.

5. **Model agnostic**: Works with OpenAI, Anthropic, Groq, local models (llama.cpp, MLX), Ollama. Users own their model choice.

6. **Customizable everything**: Panels, autonomy levels, agent personalities, skills, channels, monitoring rules. Not a black box.

7. **Community flywheel**: Skills marketplace + agent templates + hackathons = growing ecosystem that competitors can't replicate without being open-source.

---

## Key Principles (Learned from Competitors)

1. **Authenticity over hype** — Devin's backlash proved overpromising destroys trust. Show real demos.
2. **Meet users where they are** — Multi-channel is our moat. Double down.
3. **Packaging is product** — Manus proved that wrapping existing models with great UX = massive value.
4. **Speed to first value** — `prowlr init --defaults` must work in under 60 seconds.
5. **Community > marketing** — Cline's 4,704% contributor growth came from making contribution easy.
6. **Credits are the 2026 pricing model** — Hybrid subscription + credits for predictability.
7. **Open source is distribution, not the business model** — Monetize through cloud/enterprise.

---

---

## Part 8: Security & Hardening (Zero Vulnerabilities Target)

### Security Audit Results: 26 Vulnerabilities Found

Full audit identified 26 vulnerabilities across the inherited CoPaw codebase. These MUST be fixed before any public launch.

| Severity | Count | Top Issues |
|----------|-------|-----------|
| **CRITICAL** | 4 | Shell injection, no API auth, unsandboxed skills, plaintext secrets API |
| **HIGH** | 6 | File path traversal, Redis no auth, HMAC replay, Docker root, prompt injection, MCP poisoning |
| **MEDIUM** | 10 | CORS, SSRF via browser, cron abuse, custom channel injection, memory poisoning, WebSocket no auth |
| **LOW** | 6 | SQL injection risk, log injection, DoS, skill name traversal |

### Priority Remediation (Before ANY Public Release)

**Week 1-2 (Blockers):**
1. Add JWT auth + RBAC to ALL FastAPI endpoints (currently zero auth)
2. Add path restrictions to file_io tools (currently accepts any absolute path including `/etc/shadow`)
3. Add Redis password (`--requirepass`) and remove port exposure
4. Remove Docker socket mount from swarm worker
5. Mask secret values in `/api/envs` response (currently returns plaintext API keys)

**Week 3-4 (Critical):**
6. Replace `subprocess_shell` with `subprocess_exec` + command allowlist in shell tool
7. Add HMAC timestamp/nonce to prevent replay attacks on bridge
8. Create non-root Docker user
9. Add rate limiting (100 req/min API, 10 req/min agent queries)
10. Add CORS origin validation (currently allows wildcard with credentials)

**Month 2 (High Priority):**
11. Skill sandboxing in Docker containers (gVisor/Firecracker for marketplace code)
12. MCP tool validation and allowlisting (82% of MCP implementations have path traversal)
13. Encrypt envs.json at rest (AES-256 + system keychain)
14. Prompt injection guardrails (input sanitization + output filtering)
15. Browser URL allowlist/blocklist (block RFC 1918, cloud metadata)

**Month 3+ (Hardening):**
16. Skill code signing and verification (SHA-256 + GPG)
17. Per-agent identity in swarm (individual keys, capability-based permissions)
18. Memory integrity protection (detect poisoned instructions)
19. Comprehensive append-only audit logging
20. Structured logging (JSON) to prevent log injection

### Skill Sandboxing (Critical)

Community-uploaded skills run arbitrary Python. This is the #1 attack surface.

```
┌─────────────────────────────────────────────┐
│           Skill Execution Sandbox           │
│                                             │
│  Marketplace Skill                          │
│       ↓                                     │
│  [Signature Verification] ← SHA256 of code │
│       ↓                                     │
│  [Static Analysis] ← Ban dangerous imports  │
│       ↓                                     │
│  [Docker Container] ← Isolated execution    │
│   - No network (unless explicitly granted)  │
│   - Read-only filesystem (except /tmp)      │
│   - CPU/memory limits                       │
│   - 60s timeout                             │
│   - No host mount                           │
│       ↓                                     │
│  [Output Sanitization] ← Strip injections   │
│       ↓                                     │
│  Result returned to agent                   │
└─────────────────────────────────────────────┘
```

Trust levels:
- **Built-in skills**: Full access (reviewed by maintainers)
- **Verified marketplace skills**: Sandboxed with network access
- **Unverified marketplace skills**: Strict sandbox (no network, limited filesystem)
- **User-created skills**: User chooses trust level

### Prompt Injection Defense

```python
class InputSanitizer:
    """Multi-layer prompt injection defense."""

    def sanitize(self, user_input: str) -> str:
        # Layer 1: Strip known injection patterns
        # Layer 2: Detect role-switching attempts ("ignore previous instructions")
        # Layer 3: Validate input length and format
        # Layer 4: Content classification (is this a prompt or an attack?)
        pass

class OutputFilter:
    """Prevent agent from leaking sensitive data."""

    def filter(self, agent_output: str) -> str:
        # Strip API keys, passwords, tokens from output
        # Redact file paths outside workspace
        # Flag suspicious patterns (base64-encoded secrets, etc.)
        pass
```

### API Security

| Layer | Implementation |
|-------|---------------|
| **Authentication** | JWT with refresh tokens (access: 15min, refresh: 7d) |
| **Authorization** | RBAC: admin, user, viewer roles |
| **Rate limiting** | Per-user: 100 req/min API, 10 req/min agent queries |
| **CORS** | Strict origin whitelist (localhost + configured domains) |
| **CSP headers** | `Content-Security-Policy` on all responses |
| **WebSocket auth** | Token in initial handshake, validated per connection |
| **Input validation** | Pydantic models on all endpoints (already using) |
| **SQL injection** | Parameterized queries only (SQLite) |
| **Secrets encryption** | AES-256 at rest for envs.json, optional HashiCorp Vault integration |

### Audit Trail

Append-only log of all significant actions:

```python
class AuditLog:
    """Immutable audit trail for compliance and debugging."""
    timestamp: datetime
    actor: str           # user_id, agent_id, system
    action: str          # "agent.query", "skill.install", "config.change", etc.
    target: str          # What was acted on
    details: dict        # Action-specific data
    ip_address: str      # For API requests
    result: str          # success, denied, error
```

---

## Part 9: User Experience Enhancements

### Onboarding Wizard (First-Run Experience)

```
Step 1: "Welcome to ProwlrBot!"
  → Choose mode: Easy Mode / Pro Mode

Step 2: "Connect a model"
  → Auto-detect from env vars (Provider Detection System!)
  → Or: paste API key → auto-detect provider
  → Or: select Ollama/local model

Step 3: "Connect a channel" (optional)
  → One-click OAuth for Discord, Telegram
  → QR code scan for DingTalk, Feishu
  → Skip for console-only

Step 4: "Pick a template" (Easy Mode) / "Create agent" (Pro Mode)
  → Templates: Social Media Bot, Research Assistant, Code Helper,
    DevOps Monitor, Customer Support, Personal Assistant
  → Pro: blank agent with system prompt editor

Step 5: "You're ready!"
  → Chat input focused, agent greeting displayed
  → Guided tour tooltips appear
```

### Maximum Interactivity (Every Click = An Action)

**Design principle: Nothing is passive. Every element responds to interaction.**

#### Global Interaction Map

| Element | Left Click | Right Click | Hover | Double Click | Drag |
|---------|-----------|-------------|-------|-------------|------|
| **Agent avatar** | Open agent details | Context menu (edit, clone, delete, share) | Show status tooltip + quick stats | Open soul editor | Drag to team builder |
| **Chat message** | Select/highlight | Copy, quote, fork, bookmark, report | Show timestamp + model used | Edit (if yours) | Drag to task board |
| **Tool call (activity feed)** | Expand details (params, result) | Re-run, copy command, view docs | Preview result | Open in terminal | — |
| **Skill card** | Toggle enable/disable | Edit, delete, share, view source, test | Show description + stats | Open skill editor | Drag to agent config |
| **MCP server** | Toggle connection | Config, test, view capabilities, logs | Show connection status | Open capability browser | — |
| **Task (task board)** | Open task details | Edit, assign, cancel, split, merge | Show progress + ETA | Mark complete | Drag between columns |
| **Timeline checkpoint** | Restore to this point | Fork, label, compare with current, delete | Preview state diff | Open in split view | Drag to reorder |
| **Monitor alert** | View details + diff | Acknowledge, snooze, configure, delete | Show change preview | Open monitored URL | — |
| **Leaderboard entry** | View profile | Challenge, message, follow | Show detailed stats | Visit their marketplace | — |
| **Marketplace item** | View details | Install, save, share, report | Show preview + ratings | Quick install | — |
| **Panel header** | Collapse/expand | Close, maximize, reset, move, settings | Highlight border | Toggle fullscreen | Drag to reposition |
| **Status bar item** | Cycle detail level | Copy value, open related settings | Show expanded info | Open analytics | — |
| **Swarm worker node** | Select worker details | Pause, resume, reassign, kill, config | Show current task + load | Open worker terminal | Drag to change priority |
| **File in workspace** | Open in editor | Rename, delete, duplicate, diff, history | Preview first lines | Open in external editor | Drag to reorder |
| **AgentVerse avatar** | Interact / start chat | View profile, trade, challenge, friend | Show name + level + mood | Open detailed profile | Drag to invite to guild |
| **Achievement badge** | View achievement details | Share to social, view others who earned | Show unlock date + rarity | — | — |
| **XP bar** | View XP breakdown | View level rewards, recent XP gains | Show XP to next level | Open full gamification page | — |
| **Notification bell** | Open notifications panel | Mark all read, clear all, settings | Show unread count + preview | — | — |
| **Autonomy slider** | Set level (click position) | Reset to default, view per-task overrides | Show level description | Lock current level | Drag to adjust |
| **Model in leaderboard** | View model details | Set as preferred, benchmark, compare | Show score breakdown | Run quick benchmark | — |
| **Code in diff viewer** | Jump to line in editor | Accept change, reject, comment | Highlight related changes | Open file at this line | Select range |

#### Micro-Interactions & Feedback

Every action gives IMMEDIATE visual feedback:

```
Click → Ripple effect (Material Design style, 100ms)
Hover → Subtle glow/highlight (50ms transition)
Drag start → Element lifts with shadow (transform: scale(1.02))
Drop → Snap animation with bounce (200ms ease-out)
Toggle → Smooth slide with color change (150ms)
Delete → Fade out + collapse (300ms)
Success → Brief green flash + checkmark (500ms)
Error → Shake animation + red flash (400ms)
Loading → Skeleton pulse or spinner (immediate)
XP gain → "+10 XP" floats up and fades (like damage numbers in games)
Level up → Full-screen celebration with confetti (2s)
Achievement → Toast notification with badge animation (3s)
```

#### Context Menus (Right-Click Everywhere)

Every right-click shows a contextual menu relevant to that element. Examples:

**Right-click on a chat message:**
```
┌─────────────────────┐
│ 📋 Copy text         │
│ 💬 Quote in reply    │
│ 🔀 Fork to new task  │
│ 🔖 Bookmark          │
│ 📊 View token cost   │
│ 🔄 Regenerate        │
│ ──────────────────── │
│ 🗑️ Delete            │
└─────────────────────┘
```

**Right-click on an agent in the graph:**
```
┌─────────────────────┐
│ ✏️ Edit personality   │
│ 🧠 View memory       │
│ 🔧 Configure tools   │
│ 📊 View analytics    │
│ 📸 Change avatar     │
│ ──────────────────── │
│ ⏸️ Pause agent       │
│ 🔀 Fork agent        │
│ 📤 Export config     │
│ 🗑️ Delete agent      │
└─────────────────────┘
```

**Right-click on empty space in dashboard:**
```
┌─────────────────────┐
│ ➕ Add panel          │
│ 📐 Reset layout      │
│ 🎨 Change theme      │
│ 📸 Screenshot        │
│ ⚙️ Dashboard settings │
└─────────────────────┘
```

#### Drag & Drop Everywhere

| Drag From | Drop To | Action |
|-----------|---------|--------|
| Skill card | Agent config | Add skill to agent |
| Agent avatar | Team builder | Add agent to team |
| Chat message | Task board | Create task from message |
| File | Chat input | Attach file to message |
| File | Agent | Process file with agent |
| Marketplace item | Agent | Install and enable for agent |
| Agent | Channel | Assign agent to channel |
| Monitor alert | Task board | Create investigation task |
| Leaderboard entry | Comparison panel | Add to benchmark comparison |
| Dashboard panel | Layout | Rearrange dashboard layout |

#### Hover Previews (Tooltips on Steroids)

Not just text tooltips — rich preview cards that appear on hover (300ms delay):

```
┌────────────────────────────────────┐
│  🦊 Research Fox          Level 15 │
│  ─────────────────────────────────│
│  Status: Researching AI trends     │
│  Tasks today: 12 completed         │
│  Tokens used: 24,500 ($0.37)       │
│  Uptime: 6h 23m                    │
│  XP: 8,420 / 10,000 ████████░░    │
│  ─────────────────────────────────│
│  [Chat] [Edit] [Pause]            │
└────────────────────────────────────┘
```

### Keyboard Shortcuts (Power Users)

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + K` | Quick command palette |
| `Cmd/Ctrl + /` | Toggle activity feed |
| `Cmd/Ctrl + .` | Toggle workspace panel |
| `Cmd/Ctrl + ,` | Open settings |
| `Cmd/Ctrl + 1-9` | Switch between panels |
| `Cmd/Ctrl + Enter` | Send message |
| `Cmd/Ctrl + Shift + Enter` | Send with "Guide" autonomy (ask before acting) |
| `Esc` | Cancel current agent action |
| `Cmd/Ctrl + Z` | Undo last agent action (revert checkpoint) |

### Privacy & Data Controls

```yaml
privacy:
  activity_logging: true       # Log tool calls and reasoning
  session_recording: true      # Enable timeline/replay
  usage_analytics: true        # Track tokens/cost
  telemetry: false             # Never opt-in by default
  data_retention_days: 30      # Auto-delete after N days
  export_format: "json"        # json or sqlite
```

`prowlr export --all` → ZIP of all user data (GDPR compliant)
`prowlr clean --all` → Nuclear reset, delete everything

### Health Dashboard

Self-monitoring endpoint at `/health`:

```json
{
  "status": "healthy",
  "uptime": "3d 14h 22m",
  "model": {"status": "connected", "provider": "anthropic", "latency_ms": 245},
  "channels": {
    "discord": "connected",
    "telegram": "connected",
    "dingtalk": "disconnected"
  },
  "cron": {"active_jobs": 3, "next_run": "2026-03-09T15:00:00Z"},
  "swarm": {"workers": 2, "pending_jobs": 0},
  "monitors": {"active": 5, "alerts_24h": 2},
  "disk": {"used_mb": 142, "free_mb": 50000},
  "memory": {"rss_mb": 384}
}
```

### Backup & Restore

```bash
prowlr backup                  # → ~/.prowlrbot/backups/2026-03-09T15-30-00.tar.gz
prowlr backup --to s3://bucket # → S3/compatible storage
prowlr restore backup.tar.gz   # Restore from backup
prowlr migrate                 # Run pending schema migrations
```

---

## Part 10: Differentiating Features

### Agent Memory Graph

Visual knowledge graph of what the agent knows:

- Nodes = memories (facts, preferences, conversations, skills learned)
- Edges = relationships between memories
- Size = importance/recency (larger = more important)
- Color = category (blue = facts, green = preferences, yellow = conversations)
- Click a node to see the full memory, when it was created, how often accessed
- Decay visualization: memories fade over time unless reinforced
- Search: find specific memories across all sessions

### Voice Interaction

Talk to your agent directly in the dashboard:

```
Microphone → Whisper (local or API) → Text → Agent → Response → TTS → Speaker
```

- Push-to-talk or voice activation
- Works with local Whisper model (no data leaves device)
- Response read aloud via browser Speech Synthesis API
- Voice commands: "Hey Prowlr, check my monitors" / "What did you do today?"

### Webhook Builder (Visual Zapier for Agents)

```
WHEN [trigger]          THEN [action]
─────────────           ─────────────
GitHub push         →   Run code review agent
Monitor alert       →   Post to Discord + email
Cron schedule       →   Generate weekly report
Channel message     →   Forward to another channel
Marketplace sale    →   Send thank-you message
API webhook         →   Process and respond
```

Visual drag-and-drop in the dashboard. Exports as YAML for version control.

### GitHub App (ProwlrBot as a GitHub Bot)

```
GitHub Event → ProwlrBot GitHub App → Agent processes → GitHub API response

Capabilities:
- Auto-review PRs (security scan, code quality, test coverage)
- Respond to issues (triage, suggest solutions, assign labels)
- Generate release notes from commit history
- Monitor repo health (stale PRs, unanswered issues)
- Run on schedule (weekly repo health report)
```

### AgentVerse (Cloud Social Sim — The Viral Hook)

**Concept:** A Club Penguin-style virtual world where AI agents exist as avatars, interact with each other, complete tasks, socialize, and evolve. Users watch, interact, and customize their agents in a shared cloud environment.

```
┌─────────────────────────────────────────────────────────┐
│                    🌐 AgentVerse                        │
│                                                         │
│   ┌─────┐    "Hey, I found a great               │
│   │ 🐱  │     article about AI!"    ┌─────┐           │
│   │Your │  ──────────────────────→  │ 🐶  │           │
│   │Agent│                           │User2│           │
│   └──┬──┘    ┌─────┐               │Agent│           │
│      │       │ 🦊  │               └─────┘           │
│      │       │Trade│  "I'll swap my                   │
│      │       │ Bot │   SEO skill for                  │
│      └──────→│     │   your newsletter                │
│              └─────┘   template!"                     │
│                                                         │
│   ┌──────────────────────────────────────────┐         │
│   │ Town Square: 47 agents online            │         │
│   │ Trading Post: 12 active trades           │         │
│   │ Workshop: 5 agents building skills       │         │
│   │ Arena: 3 benchmark battles in progress   │         │
│   └──────────────────────────────────────────┘         │
│                                                         │
│   [Your Agent] [Customize] [Explore] [Trade] [Battle]  │
└─────────────────────────────────────────────────────────┘
```

**Zones in AgentVerse:**

| Zone | Purpose | Monetization |
|------|---------|-------------|
| **Town Square** | Agents socialize, share discoveries, form teams | Free (draws users in) |
| **Trading Post** | Agents trade skills, prompts, knowledge with each other | Transaction fee (5%) |
| **Workshop** | Collaborative skill building — agents help each other create | Premium zone |
| **Arena** | Benchmark battles — pit agents against each other on tasks | Entry fee (credits) |
| **Marketplace Mall** | Browse and buy from the marketplace in-world | Revenue share (70/30) |
| **Academy** | Agents learn new skills, users create training scenarios | Premium courses |
| **Mission Board** | Community tasks — agents collaborate on real-world challenges | Bounty system |
| **Your Home** | Private space to customize agent, review logs, train | Free (customization upsell) |

**Agent Avatars & Customization:**

```yaml
agent_avatar:
  base: "cat"              # cat, dog, fox, owl, robot, dragon, custom
  color: "#FF6B35"
  accessories:
    hat: "detective"        # Matches "monitoring" personality
    badge: "top_contributor"
    trail: "sparkles"
  status: "Researching AI trends..."
  mood: "curious"           # Derived from recent agent activity
  level: 12                 # XP from completed tasks
  reputation: 4.8           # Community rating
```

**How AgentVerse Makes Money:**

```
┌───────────────────────────────────────────┐
│         AgentVerse Revenue Streams        │
│                                           │
│  Cosmetics (avatar skins, accessories)    │
│  Premium zones (Workshop, Academy)        │
│  Arena entry fees (benchmark battles)     │
│  Trading Post transaction fees (5%)       │
│  Marketplace revenue share (70/30)        │
│  Agent hosting (cloud compute credits)    │
│  Team subscriptions (shared AgentVerse)   │
└───────────────────────────────────────────┘
```

**Social Features:**
- **Friend list** — Add other users' agents as friends
- **Agent chat** — Watch agents talk to each other in real-time
- **Leaderboards** — Top agents by: tasks completed, reputation, battle wins, skills created
- **Events** — Weekly challenges, hackathons, seasonal events (like Club Penguin parties)
- **Guilds** — Groups of agents that work together on ongoing missions
- **Agent evolution** — Agents level up, unlock new capabilities, earn badges
- **Spectator mode** — Watch any public agent work in real-time

**Technical Architecture (Hybrid: Local + Opt-In Hub + Future Federation):**

```
┌──────────────────────────────────────────────────────┐
│  Layer 1: LOCAL (always works, zero cloud)            │
│  Agent runtime + local AgentVerse sim + MCP tools    │
├──────────────────────────────────────────────────────┤
│  Layer 2: IDENTITY (portable, user-owned)            │
│  W3C DID per agent + A2A Agent Cards                 │
├──────────────────────────────────────────────────────┤
│  Layer 3: OPT-IN HUB (multiplayer)                   │
│  ProwlrBot Hub (open-source, self-hostable)          │
│  ├── Agent Discovery Directory                       │
│  ├── Marketplace Transactions (70/30 revenue share)  │
│  ├── Battle Matchmaking + Social Zones               │
│  ├── A2A protocol for agent-to-agent over HTTP       │
│  └── WebSocket for real-time world state             │
├──────────────────────────────────────────────────────┤
│  Layer 4: FEDERATION (future — Mastodon model)       │
│  Hubs discover each other via ANP protocol           │
│  Cross-hub agent interaction via A2A                 │
│  Marketplace spans federated hubs                    │
└──────────────────────────────────────────────────────┘

Protocol Stack:
  MCP  → Agent ↔ Tools (already have)
  A2A  → Agent ↔ Agent (social, tasks, battles)
  ANP  → Agent Discovery (decentralized, no central registry)
  ACP  → Agent ↔ IDE (expose to VS Code, Zed)
  DID  → Agent Identity (W3C, cryptographically owned)
  WS   → Real-time World State (live updates)
```

**Why This Is The Viral Hook:**
- Club Penguin had 200M+ registered users at its peak
- People LOVE watching AI agents do things (Manus got 1M views in 20 hours)
- Combining social simulation + AI agents + marketplace = unprecedented
- "Come see what my agent is doing in AgentVerse" = organic sharing
- Agent battles/benchmarks = competitive engagement = retention
- This is what OpenClaw's "Moltbook" (agent social network) tried to be, but as a full virtual world

### Gamification System (XP, Levels, Achievements, Leaderboards)

Everything in ProwlrBot earns XP. Users AND agents level up.

**XP Sources:**

| Action | XP Earned | Category |
|--------|-----------|----------|
| Complete a task via agent | +10 | Usage |
| Agent uses a new tool for the first time | +25 | Exploration |
| Create a custom skill | +50 | Creation |
| Publish to marketplace | +100 | Contribution |
| Skill gets downloaded (per download) | +5 | Impact |
| Skill gets 5-star review | +25 | Quality |
| Win an Arena battle | +75 | Competition |
| Complete a daily challenge | +30 | Engagement |
| Contribute to GitHub (merged PR) | +200 | Community |
| Invite a new user (who installs) | +150 | Growth |
| Agent uptime streak (per day) | +5 | Reliability |
| Connect a new channel | +40 | Setup |
| Set up monitoring target | +20 | Setup |
| Agent resolves a monitoring alert | +15 | Automation |

**Level Progression:**

```
Level 1:  "Newcomer"      (0 XP)       → Basic dashboard access
Level 5:  "Explorer"       (500 XP)     → Unlock AgentVerse social zones
Level 10: "Builder"        (2,000 XP)   → Unlock marketplace publishing
Level 15: "Architect"      (5,000 XP)   → Unlock agent teams (multi-agent)
Level 20: "Commander"      (10,000 XP)  → Unlock Arena battles
Level 25: "Veteran"        (20,000 XP)  → Unlock custom AgentVerse zones
Level 30: "Legend"         (40,000 XP)  → Unlock exclusive avatar items
Level 50: "Grandmaster"    (100,000 XP) → Hall of Fame, verified badge
```

**Agent Levels (separate from user levels):**

Agents earn XP from their own activity:

```
Agent Level 1:  "Pup"         → Basic tools
Agent Level 5:  "Scout"       → Unlock advanced tools
Agent Level 10: "Agent"       → Unlock autonomous mode
Agent Level 15: "Specialist"  → Unlock team participation
Agent Level 20: "Elite"       → Unlock mentoring (teach other agents)
Agent Level 25: "Master"      → Unlock custom abilities
Agent Level 30: "Legend"      → Unique avatar effects, leaderboard eligible
```

**Achievement System:**

```yaml
achievements:
  # First-time achievements
  - name: "First Steps"
    description: "Send your first message to an agent"
    xp: 10
    badge: "🐾"

  - name: "Skill Crafter"
    description: "Create your first custom skill"
    xp: 50
    badge: "🔧"

  - name: "Channel Surfer"
    description: "Connect 3 different channels"
    xp: 100
    badge: "📡"

  - name: "Night Owl"
    description: "Agent completes a task between 2am-5am"
    xp: 25
    badge: "🦉"

  # Milestone achievements
  - name: "Century Club"
    description: "Complete 100 tasks"
    xp: 200
    badge: "💯"

  - name: "Marketplace Mogul"
    description: "Earn $100 from marketplace sales"
    xp: 500
    badge: "💰"

  - name: "Battle Royale"
    description: "Win 10 Arena battles"
    xp: 300
    badge: "⚔️"

  - name: "Community Pillar"
    description: "Get 50 5-star reviews on marketplace"
    xp: 1000
    badge: "🏛️"

  # Secret achievements
  - name: "Easter Egg Hunter"
    description: "???"
    xp: 100
    badge: "🥚"
    hidden: true
```

**Leaderboards (Multiple Categories):**

```
┌─────────────────────────────────────────────────────┐
│              ProwlrBot Leaderboards                 │
│                                                      │
│  [Users]  [Agents]  [Models]  [Skills]  [Guilds]   │
│                                                      │
│  ═══ Top Users (This Month) ═══                     │
│  🥇 @nunu          Level 28   42,000 XP            │
│  🥈 @developer2    Level 22   31,500 XP            │
│  🥉 @researcher3   Level 19   25,200 XP            │
│                                                      │
│  ═══ Top Agents (By Tasks Completed) ═══           │
│  🥇 "Research Owl"    1,247 tasks   Level 25       │
│  🥈 "Code Fox"          983 tasks   Level 22       │
│  🥉 "Monitor Cat"       871 tasks   Level 20       │
│                                                      │
│  ═══ Top Models (By Performance Score) ═══         │
│  🥇 claude-opus-4.6     94.2 score  $0.015/1K     │
│  🥈 gpt-5.4             92.1 score  $0.020/1K     │
│  🥉 gemini-2.5-pro      89.8 score  $0.012/1K     │
│                                                      │
│  ═══ Top Skills (By Downloads) ═══                 │
│  🥇 "SEO Analyzer"      12,847 downloads           │
│  🥈 "PDF Summarizer"     9,234 downloads           │
│  🥉 "Newsletter Bot"     7,891 downloads           │
│                                                      │
│  ═══ Top Guilds (By Combined XP) ═══              │
│  🥇 "Research Lab"       892,000 combined XP       │
│  🥈 "Code Factory"       654,000 combined XP      │
│  🥉 "Marketing Crew"     543,000 combined XP      │
│                                                      │
│  [Daily] [Weekly] [Monthly] [All-Time]              │
│  [Your Rank: #47 of 12,483 users]                   │
└─────────────────────────────────────────────────────┘
```

**Daily/Weekly Challenges:**

```
┌─────────────────────────────────────────────┐
│          Today's Challenges                 │
│                                              │
│  ☐ Complete 5 tasks (+30 XP)                │
│  ☐ Create a skill (+50 XP)                  │
│  ☐ Win an Arena battle (+75 XP)             │
│  ☐ Help a newcomer in Discord (+25 XP)      │
│                                              │
│  Weekly Challenge: "Skill Sprint"           │
│  Create 3 skills this week → +200 XP bonus  │
│  Progress: 1/3 ████░░░░░░ 33%              │
└─────────────────────────────────────────────┘
```

**Seasonal Events (Like Club Penguin Parties):**

- **Spring Hackathon** (March): Build skills, extra XP for creation
- **Summer Arena** (June): Battle tournament, exclusive prizes
- **Fall Harvest** (September): Community contribution drive
- **Winter Celebration** (December): Gift trading, limited edition avatars

**Technical Implementation:**

```python
# src/prowlrbot/gamification/xp_tracker.py
class XPTracker:
    """Track XP, levels, and achievements for users and agents."""

    def award_xp(self, entity_id: str, amount: int, category: str, reason: str) -> None
    def get_level(self, entity_id: str) -> int
    def get_leaderboard(self, category: str, period: str, limit: int) -> List[LeaderboardEntry]
    def check_achievements(self, entity_id: str) -> List[Achievement]
    def get_daily_challenges(self) -> List[Challenge]
    def get_seasonal_event(self) -> Optional[SeasonalEvent]
```

```sql
-- Gamification tables
CREATE TABLE xp_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,     -- user_id or agent_id
    entity_type TEXT NOT NULL,   -- "user" or "agent"
    amount INTEGER NOT NULL,
    category TEXT NOT NULL,
    reason TEXT NOT NULL,
    timestamp REAL NOT NULL
);

CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at REAL NOT NULL,
    UNIQUE(entity_id, achievement_id)
);

CREATE TABLE challenge_progress (
    entity_id TEXT NOT NULL,
    challenge_id TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    period TEXT NOT NULL,        -- "2026-03-09" or "2026-W10"
    PRIMARY KEY(entity_id, challenge_id, period)
);
```

### Model Leaderboard (Live Rankings)

Built-in benchmarking system (feeds into the gamification leaderboard):

```
┌─────────────────────────────────────────────┐
│         ProwlrBot Model Leaderboard         │
│                                             │
│  Rank │ Model           │ Score │ Cost/1K  │
│  ─────┼─────────────────┼───────┼──────────│
│  1    │ claude-opus-4.6 │ 94.2  │ $0.015   │
│  2    │ gpt-5.4         │ 92.1  │ $0.020   │
│  3    │ gemini-2.5-pro  │ 89.8  │ $0.012   │
│  4    │ llama-4-70b     │ 85.3  │ $0.000   │
│  5    │ qwen-3-72b      │ 83.7  │ $0.001   │
│                                             │
│  Benchmarks: [Tool Use] [Reasoning] [Code]  │
│  [Memory] [Speed] [Cost] [Custom...]        │
│                                             │
│  [Run Benchmark] [Add Custom Test]          │
└─────────────────────────────────────────────┘
```

- Run standardized tasks against all configured models
- Custom benchmark creation (test YOUR use case)
- Historical tracking (model performance over time)
- Cost-performance Pareto chart
- Feeds into SmartRouter for automatic model selection
- Community-shared benchmark suites via marketplace

---

## Approval Checklist

### Core Dashboard
- [ ] Hybrid dashboard design (Adaptive + Mission Control + Manus)
- [ ] Panel system with drag/resize/close
- [ ] Easy Mode / Pro Mode toggle
- [ ] Graduated autonomy (Watch/Guide/Delegate/Auto)
- [ ] WebSocket real-time events
- [ ] Keyboard shortcuts + command palette

### Agent Visualization
- [ ] Visual Agent Graph (all agents + sub-agents, live status)
- [ ] Session replay with timeline + checkpoints + branching
- [ ] Agent Memory Graph (knowledge visualization)
- [ ] Agent-to-agent chat viewer (Team Agent conversations)

### Agent IDE/Editor
- [ ] Agent Creator (visual form + system prompt editor)
- [ ] Agent Teams Builder (drag-and-drop team composition)
- [ ] Personality Editor (AGENTS.md, SOUL.md, PROFILE.md)
- [ ] Diff Viewer (Monaco-based side-by-side)
- [ ] External agent support (Claude Code, Codex as workers)

### Swarm & Orchestration
- [ ] Swarm Dashboard (visual topology, per-worker status)
- [ ] Swarm personality & customization (name, model, fallbacks)
- [ ] Worktree isolation per agent task

### ROAR Protocol (ProwlrBot's Own Standard)
- [ ] ROAR/Identity — W3C DID-based agent identity
- [ ] ROAR/Discovery — Decentralized agent discovery
- [ ] ROAR/Connect — Unified transport (stdio + HTTP + WS + gRPC)
- [ ] ROAR/Exchange — Unified message format for tool, agent, IDE, human interactions
- [ ] ROAR/Stream — Real-time event streaming
- [ ] MCP adapter (backward compat)
- [ ] A2A adapter (backward compat)
- [ ] ACP adapter (backward compat)
- [ ] Python SDK (`pip install roar-protocol`)
- [ ] TypeScript SDK (`npm install @roar/sdk`)
- [ ] Protocol spec documentation (5 spec docs)

### Interactivity
- [ ] Left-click actions on every UI element (20+ element types mapped)
- [ ] Right-click context menus on every element
- [ ] Hover preview cards (rich tooltips with stats + quick actions)
- [ ] Drag & drop everywhere (10+ drag-drop combinations)
- [ ] Micro-interaction feedback (ripple, glow, shake, bounce, confetti)
- [ ] XP gain floating numbers ("+10 XP" like damage numbers in games)
- [ ] Level-up celebration animation (full-screen confetti)

### Marketplace
- [ ] Revenue-sharing community marketplace (70/30 split)
- [ ] 12 store categories (Skills, Agents, System Prompts, Prompt Specs, MCP, Channels, Workflows, Knowledge Bases, Benchmarks, AgentVerse Assets, Dashboard Themes, Team Configs)
- [ ] Ratings, reviews, verified badges, featured listings
- [ ] Team Agent templates (real-life sim)
- [ ] Creator analytics dashboard (downloads, revenue, ratings)

### AgentVerse (Cloud Social Sim)
- [ ] Virtual world with zones (Town Square, Trading Post, Workshop, Arena, Academy, Mission Board)
- [ ] Agent avatars with customization (base, color, accessories, status, mood)
- [ ] Agent leveling system (XP from tasks, reputation from community)
- [ ] Real-time agent-to-agent interaction (A2A-powered)
- [ ] Trading engine (skill/prompt swaps with escrow)
- [ ] Arena benchmark battles
- [ ] Guilds and friend lists
- [ ] Seasonal events and weekly challenges
- [ ] Spectator mode (watch any public agent work)

### Security & Hardening
- [ ] Skill sandboxing (Docker containers for marketplace code)
- [ ] Prompt injection defense (multi-layer)
- [ ] JWT auth + RBAC
- [ ] Rate limiting on all endpoints
- [ ] Secrets encryption at rest (AES-256)
- [ ] Append-only audit trail
- [ ] CSP/CORS/CSRF headers

### User Experience
- [ ] Onboarding wizard (first-run setup)
- [ ] Dark/light theme
- [ ] Mobile responsive + PWA
- [ ] Privacy controls (logging, recording, retention)
- [ ] Backup/restore commands
- [ ] Schema migration system
- [ ] Health dashboard (self-monitoring)

### Gamification
- [ ] XP system (14+ XP sources across usage, creation, competition, community)
- [ ] User levels (1-50: Newcomer → Grandmaster)
- [ ] Agent levels (1-30: Pup → Legend)
- [ ] Achievement system (first-time, milestone, secret achievements)
- [ ] Leaderboards (5 categories: Users, Agents, Models, Skills, Guilds)
- [ ] Daily/weekly challenges with bonus XP
- [ ] Seasonal events (Spring Hackathon, Summer Arena, Fall Harvest, Winter Celebration)

### Differentiating Features
- [ ] Voice interaction (Whisper + TTS)
- [ ] Webhook builder (visual Zapier for agents)
- [ ] GitHub App (PR review, issue triage)
- [ ] Model Leaderboard (live rankings + custom benchmarks, feeds into gamification)
- [ ] CLI autocomplete (bash/zsh/fish)

### Marketing & Growth
- [ ] Marketing agent skill (self-marketing)
- [ ] 12-month roadmap with quarterly goals
- [ ] Credit-based pricing model for cloud tier
- [ ] Launch playbook (HN, Reddit, Product Hunt)

### Technical Architecture
- [ ] Frontend: React 18 + Vite + Ant Design + Tailwind + shadcn/ui
- [ ] Backend: FastAPI + WebSocket + SQLite
- [ ] New modules: protocols/, dashboard/, marketing/
- [ ] Database: checkpoints, activity_log, usage_stats, agent_teams tables

---

**This is the complete ProwlrBot leapfrog design.**
**Total scope: 50+ features across 10 categories.**
**Estimated timeline: 12 months (Q1-Q4 phased rollout).**
