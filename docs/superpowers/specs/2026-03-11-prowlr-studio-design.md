# Prowlr-Studio Design Spec

**Date:** 2026-03-11
**Status:** Draft
**Scope:** Rebrand ShipSec Studio to Prowlr-Studio, fix security vulnerabilities, transform into ProwlrBot's agent orchestration frontend.

---

## 1. What We're Building

Prowlr-Studio is ProwlrBot's visual frontend — a full agent workspace where you see every agent, watch them work in real-time, control their autonomy, build multi-agent workflows, and manage the entire platform from one UI.

It replaces ProwlrBot's existing React console (port 8088) with a production-grade TypeScript application built on React 19, Radix/shadcn, Tailwind, ReactFlow, xterm.js, and Monaco editor.

**Source:** Fork of ShipSec Studio (Apache 2.0). Repository: `github.com/ProwlrBot/prowrl-studio`.

---

## 2. Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Studio role | Full Studio (workflow builder + live dashboard + agent management) | Most differentiated product; existing codebase supports all three |
| Security components | Move to marketplace as optional plugin pack | Keeps default UX agent-focused; security teams can install from prowlr-marketplace |
| Authentication | Pluggable: ProwlrBot JWT default, Clerk optional | No third-party dep by default; Clerk available for teams wanting managed auth; clear docs on switching |
| Infrastructure | Progressive enhancement: SQLite+filesystem default, add services as needed | Matches ProwlrBot's "pip install and go" philosophy |
| Console relationship | Studio replaces console (phased) | One app, one stack, no Frankenstein; console pages are simple CRUD, easy to rebuild |
| MCP UI | Built-in (already exists in Studio) + MCP server packs as marketplace plugins | MCP Library page, server CRUD, tool discovery, group bundling all already built |

---

## 3. Architecture

Two backends, one frontend. Python handles agents/channels/providers/ROAR. TypeScript handles workflows/execution/studio UI. They communicate via REST + webhooks and share JWT auth tokens.

**ProwlrBot Backend (Python/FastAPI :8088):** Agent Runner, Channel Manager, MCP Client Manager, Provider Router, ROAR + A2A Server, Monitor Engine, Cron Scheduler, plus new `/api/studio/*` proxy endpoints.

**Prowlr-Studio Backend (TypeScript/NestJS :3211):** Workflow CRUD + DSL Compiler, Execution Management, Trace + Event Ingestion, MCP Server Management, Secrets Store (AES-256-GCM), Human-in-the-Loop Gates, Artifact Storage, Auth (JWT/Clerk/API keys).

**Studio Worker (Bun):** Component Execution, Docker Container Runner, Playwright Browser Instances, PTY Terminal Streaming. Optional Temporal integration for durable workflows.

### 3.1 Backend Integration Contract

The two backends communicate via REST and SSE. ProwlrBot is the source of truth for agents, channels, and providers. Studio is the source of truth for workflows, executions, and UI state.

**ProwlrBot exposes to Studio (REST, port 8088):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/agents` | GET | List all agents with status, config, capabilities |
| `/api/agents/{id}/run` | POST | Start an agent run, returns `run_id` |
| `/api/agents/{id}/stop` | POST | Stop a running agent |
| `/api/agents/{id}/message` | POST | Send human message to running agent |
| `/api/agents/{id}/stream` | GET (SSE) | Real-time agent event stream (see 3.2) |
| `/api/agents/{id}/autonomy` | PUT | Change autonomy level mid-run |
| `/api/channels` | GET/POST/PUT/DELETE | Channel CRUD |
| `/api/providers` | GET | Available providers + health |
| `/api/monitors` | GET/POST/PUT/DELETE | Monitor CRUD |
| `/api/crons` | GET/POST/PUT/DELETE | Cron job CRUD |
| `/api/mcp/clients` | GET | MCP client connections |
| `/api/auth/validate` | POST | Validate JWT token (Studio calls this) |
| `/api/auth/token` | POST | Issue JWT token (login) |

**Studio exposes to ProwlrBot (REST, port 3211):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/webhooks/agent-event` | POST | ProwlrBot pushes agent events for trace storage |
| `/api/webhooks/workflow-trigger` | POST | Trigger workflow from channel/monitor/cron |

**JWT validation flow:** Studio's NestJS `AuthGuard` receives JWT from the browser, then calls `PROWLRBOT_API_URL/api/auth/validate` to verify it against ProwlrBot's signing key. ProwlrBot returns `{ valid: true, user: { id, role } }` or `401`. Studio caches validation for 5 minutes (configurable via `JWT_CACHE_TTL`). When `AUTH_PROVIDER=clerk`, Studio validates directly against Clerk's JWKS endpoint instead.

### 3.2 Agent Event Stream Protocol

The Agent Workspace's 12 tabs are powered by a single SSE connection per agent at `/api/agents/{id}/stream`. Events are JSON with a `type` field that maps to tabs:

| Event Type | Tab(s) | Payload |
|------------|--------|---------|
| `thought` | Reasoning | `{ step, content, decision, timestamp }` |
| `tool_call` | Tools | `{ tool, inputs, outputs, duration_ms, tokens }` |
| `tool_start` | Tools | `{ tool, inputs, timestamp }` |
| `terminal_output` | Terminal | `{ data: base64 }` (PTY bytes) |
| `terminal_input` | Terminal | `{ data: base64 }` (user sends via POST) |
| `browser_screenshot` | Screen, Browser | `{ url, png_base64, width, height }` |
| `browser_action` | Browser | `{ action, selector, value }` |
| `file_change` | Files, Code | `{ path, op: create/modify/delete, content?, diff? }` |
| `chat_message` | Chat | `{ from: agent/human, content }` |
| `memory_update` | Memory | `{ op: add/remove/compact, entry }` |
| `cost_update` | Cost | `{ tokens_in, tokens_out, cost_usd, model, total_cost }` |
| `log` | Logs | `{ level, message, timestamp, metadata }` |
| `config_change` | Config | `{ field, old_value, new_value }` |
| `status` | All | `{ state: running/paused/stopped/error, message? }` |

**"Take Control" mechanics:** User clicks "Take Control" on Screen or Browser tab. Studio sends `POST /api/agents/{id}/autonomy` with `level: "watch"` to pause autonomous actions. User interactions (clicks, keystrokes) are sent via `POST /api/agents/{id}/browser/input` or `POST /api/agents/{id}/terminal/input`. Click "Release Control" to restore previous autonomy level.

**State persistence:** Agent run state is persisted to ProwlrBot's SQLite (or PostgreSQL) as `agent_runs` table with `run_id`, `agent_id`, `status`, `started_at`, `ended_at`, `cost_total`, `tokens_total`. Individual events are stored in Studio's trace database for timeline replay.

**Without Redis fallback:** When Redis is absent, PTY streaming uses in-process queues (limits to single-worker mode). Browser screenshots are sent directly via SSE instead of pub/sub. MCP session tokens use SQLite. This means no horizontal scaling of workers, but single-user local dev works fine.

### 3.3 Progressive Infrastructure (with fallbacks)

| Service | Default | What It Unlocks | Without It |
|---------|---------|-----------------|------------|
| SQLite | Yes (zero config) | Workflows, traces, secrets, basic storage | N/A (always present) |
| Filesystem | Yes | Artifact storage, file uploads | N/A (always present) |
| Docker | Required for Agent Workspace | Container isolation, Playwright browsers, PTY | Agent Workspace tabs disabled; workflow builder and hub still work |
| Redis | Optional | Multi-worker PTY relay, pub/sub screenshots, rate limiting | Single-worker mode; in-process queues; MCP tokens in SQLite |
| Temporal | Optional | Durable workflow execution, retries, sub-workflows | Workflows run in-process via Bun worker (no retry/durability guarantees) |
| MinIO | Optional | Large artifact storage (S3-compatible) | Filesystem storage (local disk) |
| Kafka/Redpanda | Optional | Telemetry at scale, log aggregation | Direct SQLite trace writes (fine for < 10 agents) |
| PostgreSQL | Optional | Production database (replaces SQLite for scale) | SQLite (fine for < 100 workflows, single-node) |

---

## 4. Agent Workspace

The core feature. Each agent gets a full computer-like workspace visible in the Studio.

### 4.1 Per-Agent Workspace

Each running agent has:
- Isolated Docker container with Playwright browser instance
- PTY terminal session streaming via Redis to SSE
- Live browser screenshots streamed to UI
- File workspace visible in file tree
- Monaco editor view of files being written in real-time

### 4.2 Tabs (12 per agent)

| Tab | Content |
|-----|---------|
| Screen | Live agent desktop/browser view (VNC-style). Click "Take Control" to interact directly |
| Code | Monaco editor showing files being read/written in real-time with live diffs |
| Terminal | Full xterm.js PTY. See commands, send input |
| Browser | Agent's Playwright browser. See navigation, clicks, scrolls. Take over |
| Files | File tree of agent workspace. Created/modified/deleted files. Download artifacts |
| Reasoning | Step-by-step agent thinking. Each thought, decision, action traced. Timeline scrubber replay |
| Tools | Every tool call with inputs/outputs. Expandable JSON. Filter by type. Timing |
| Chat | Message agent mid-run. Give instructions, ask questions, provide context |
| Memory | Agent memory entries. Context window usage, token budget. CRUD |
| Cost | Real-time cost: tokens in/out, price per call, running total, budget alerts, per-model pricing |
| Logs | Structured log stream. Filter by level. Search. Export. Timeline correlation |
| Config | Agent settings: model, provider, autonomy, skills, MCP servers, channels, triggers. Edit live |

### 4.3 Layout Modes

Users can arrange agent workspaces freely:
- **Tile** -- Equal grid, all agents visible
- **Stack** -- Tabs, one agent at a time
- **Float** -- Drag windows anywhere, resize freely
- **Split** -- One main + others stacked in sidebar
- **Picture-in-Picture** -- Main agent + floating mini views
- **Focus + Timeline** -- One full-screen with scrubber

### 4.4 Controls (always visible bottom bar)

- Pause / Stop / Take Control / Message Agent buttons
- Autonomy level dropdown (Watch / Guide / Delegate / Autonomous)
- Model + provider display
- Running cost + tokens + runtime

### 4.5 Collaboration Canvas

A shared workspace where multiple agents' outputs converge. The canvas is a dedicated view (not a per-agent tab) accessible from the top nav.

**How it works:**
- Agents publish findings via ROAR `share_finding` messages. Each finding has: `agent_id`, `type` (text/code/image/link/file), `content`, `confidence`, `tags`.
- The canvas renders findings as cards in a timeline or board layout. Cards are grouped by topic/tag and linked to their source agent's workspace.
- Human can: approve/reject findings, add annotations, redirect an agent ("investigate this further"), merge findings into a summary, export as report.
- Canvas state persists per-session in ProwlrBot's SQLite via the existing `shared_context` mechanism in ProwlrHub.

**Phase 1 scope:** Read-only view of agent findings with approve/reject. Full editing and export in Phase 2.

---

## 5. Agent Hub

The agent discovery and management page.

### 5.1 Agent Cards

Grid of all agents (installed + available from marketplace). Each card shows: avatar/icon, name, description, capability tags, status indicator (running/idle/error), quick actions (Run, View Live, Configure), current task (if running).

### 5.2 Team Cards

Agent groups displayed as team cards. Shows member agents, team status, "Manage Team" action.

### 5.3 Marketplace Integration

Dashed-border cards for marketplace agents with "Install" / "Preview" actions. MCP server packs as installable plugins. Security scan pack lives in marketplace repo.

---

## 6. Workflow Builder

Existing ReactFlow-based visual workflow builder, adapted for ProwlrBot.

### 6.1 Keep As-Is
- ReactFlow canvas with drag-and-drop
- Undo/redo (Zustand + zundo)
- Design mode / Execution mode toggle
- Node config panel, validation dock
- Graph to DSL compiler
- Import/export workflows

### 6.2 Change
- Replace ShipSec security components with ProwlrBot component categories:
  - **Agent** -- ProwlrBot agent nodes (code-reviewer, research, deploy, etc.)
  - **Skill** -- Built-in skills (shell, file_io, browser, pdf, news, etc.)
  - **Channel** -- Channel nodes (Discord, Telegram, console, etc.)
  - **Monitor** -- Web/API monitor trigger nodes
  - **MCP** -- MCP server tool nodes (keep existing MCP integration)
  - **AI** -- LLM generate, AI agent (keep existing)
  - **Core** -- Entry point, text, HTTP, logic, file ops (keep existing)
  - **Notification** -- Slack, email, webhook (keep existing)
- Component author type: `'shipsecai'` to `'prowlrbot'`

### 6.3 New Components

| Component | Inputs | Outputs | Description |
|-----------|--------|---------|-------------|
| `prowlrbot.agent` | `agent_id: string`, `query: string`, `autonomy?: string`, `timeout_s?: number` | `response: string`, `artifacts: File[]`, `cost: CostSummary`, `run_id: string` | Wraps a ProwlrBot agent as a workflow node |
| `prowlrbot.channel-trigger` | `channel: string`, `filter?: regex` | `message: string`, `sender: string`, `channel_id: string`, `metadata: object` | Entry point: triggers workflow from channel message |
| `prowlrbot.monitor-trigger` | `monitor_id: string`, `severity?: string[]` | `alert: MonitorAlert`, `diff: string`, `url: string` | Entry point: triggers workflow from monitor alert |
| `prowlrbot.roar-message` | `target_agent: string`, `message: string`, `protocol?: string` | `response: string`, `status: string` | Send/receive ROAR protocol messages between agents |
| `prowlrbot.hub-task` | `action: create/claim/complete/fail`, `task_id?: string`, `description?: string` | `task_id: string`, `status: string`, `assigned_to?: string` | Create/claim/complete ProwlrHub tasks |

---

## 7. Pages (Studio replaces Console)

### 7.1 Existing Studio Pages (keep + rebrand)
Workflows list, Workflow builder (design + execution), MCP Library browser, Secrets manager, API Keys manager, Integrations manager, Schedules manager, Webhooks manager, Action Center (human-in-the-loop queue), Artifacts browser.

### 7.2 New Pages (rebuild from console)
- **Agent Hub** -- Agent cards grid, teams, marketplace integration
- **Agent Workspace** -- Multi-agent live view with 12 tabs per agent
- **Chat** -- Rebuild console chat page in Studio's UI system
- **Channels** -- Rebuild channel config forms
- **Settings** -- Rebuild model selector, env vars, provider config
- **Monitors** -- Rebuild monitor management
- **Cron** -- Rebuild cron job manager

### 7.3 Phase Plan
- **Phase 1:** Rebrand + security fixes + ship with existing Studio pages + Agent Hub + Agent Workspace
- **Phase 2:** Rebuild Chat, Channels, Settings, Monitors, Cron in Studio
- **Phase 3:** Retire old console. Studio is the only frontend.

---

## 8. Rebranding Scope

400+ references across 100+ files. Automated via find-and-replace scripts.

### 8.1 Key Replacements

| From | To |
|------|----|
| `ShipSec Studio` | `Prowlr-Studio` |
| `ShipSec` / `Shipsec` | `ProwlrBot` |
| `ShipSecAI` / `shipsecai` | `ProwlrBot` / `prowlrbot` |
| `@shipsec/*` | `@prowlrbot/*` |
| `shipsec-studio` | `prowlrbot-studio` |
| `ghcr.io/shipsecai/*` | `ghcr.io/prowlrbot/*` |
| `SHIPSEC_*` | `PROWLRBOT_*` |
| `shipsec-*` (containers) | `prowlrbot-*` |
| `studio.shipsec.ai` | `studio.prowlrbot.com` |
| `github.com/ShipSecAI/studio` | `github.com/ProwlrBot/prowrl-studio` |
| `shipsecWorkflowRun` | `prowlrbotWorkflowRun` |
| `type: 'shipsecai'` | `type: 'prowlrbot'` |

### 8.2 Categories
1. Package names (7 files)
2. Docker images/containers (12 files, 60+ changes)
3. Environment variables (30+ locations)
4. Database names/credentials (15+ locations)
5. Temporal queue names (20+ locations)
6. Kafka client IDs (25+ locations)
7. Frontend UI text + meta tags (35+ instances)
8. URLs and documentation (40+ instances)
9. Component author metadata (60+ instances in worker)
10. License/certificates (5 files)
11. Test files (20+ files)

---

## 9. Security Fixes

21 findings from audit. All fixed before first deploy.

### 9.1 Critical (fix immediately)

| ID | Issue | Fix |
|----|-------|-----|
| C1 | Default admin/admin credentials | Remove fallback. Require explicit config. Refuse to start in production with defaults |
| C2 | Hardcoded encryption keys in source | Fatal error if SECRET_STORE_MASTER_KEY unset in production. Remove FALLBACK_DEV_KEY and DEFAULT_DEV_KEY. Add .env.docker to .gitignore |
| C3 | Privileged Docker-in-Docker, TLS disabled | Enable TLS for DinD. Isolate on dedicated network |
| C4 | Timing-vulnerable internal token comparison | Replace !== with crypto.timingSafeEqual() in auth.guard.ts |

### 9.2 High (fix before deploy)

| ID | Issue | Fix |
|----|-------|-----|
| H1 | JWT token preview logged | Log token fingerprint hash instead of prefix |
| H2 | ADMIN role fallback for missing org_role | Default to MEMBER when org_role absent |
| H3 | Public ensure-tenant with weak token auth | Reject when INTERNAL_SERVICE_TOKEN not configured. Use timingSafeEqual |
| H4 | No file upload validation | Validate size, whitelist MIME types, sanitize filenames |
| H5 | Session cookie secure flag conditional | Set secure=true whenever request is HTTPS |
| H6 | No security headers | Add helmet middleware to NestJS. Add headers in nginx config |

### 9.3 Medium (fix in first sprint)

| ID | Issue | Fix |
|----|-------|-----|
| M1 | Hardcoded DB credentials in Docker Compose | Use env var substitution from .env file |
| M2 | OpenSearch security disabled | Enable security plugin by default |
| M3 | Command injection in volume cleanup | Use spawn() instead of string-interpolated exec() |
| M4 | Plaintext admin password comparison | Hash with bcrypt, compare with bcrypt.compare() |
| M5 | Webhook relies on path unguessability | Add HMAC signature verification |
| M6 | Dev session secret fallback | Generate random secret at startup when not configured |
| M7 | Broad CORS origins in production | Environment-based CORS. Production allows only configured domains |

### 9.4 Low (fix when convenient)

| ID | Issue | Fix |
|----|-------|-----|
| L1 | Swagger exposed in production | Disable or auth-gate in production |
| L2 | Testing module auto-enabled | Require explicit ENABLE_TESTING_MODULE=true |
| L3 | Content-Disposition header injection | Use RFC 5987 encoding for filenames |
| L4 | ETag disabled | Re-enable for caching benefits |

---

## 10. Auth Integration Guide

### 10.1 Default: ProwlrBot JWT
Studio authenticates against ProwlrBot's FastAPI backend. Single sign-on between Python and TypeScript backends.

```
AUTH_PROVIDER=prowlrbot
PROWLRBOT_API_URL=http://localhost:8088
```

### 10.2 Optional: Clerk
For teams wanting managed multi-tenant auth with SSO, RBAC, and user management.

```
AUTH_PROVIDER=clerk
CLERK_SECRET_KEY=sk_live_...
CLERK_PUBLISHABLE_KEY=pk_live_...
```

### 10.3 Why Switch

| Factor | ProwlrBot JWT | Clerk |
|--------|--------------|-------|
| Setup | Zero: uses existing ProwlrBot auth | Requires Clerk account + config |
| Multi-tenant | No (single operator) | Yes (orgs, teams, roles) |
| SSO | No | Yes (Google, GitHub, SAML) |
| Cost | Free | Free tier + paid plans |
| Best for | Solo users, local dev | Teams, SaaS deployments |

---

## 11. Marketplace Integration

### 11.1 Agent Marketplace
Browse and install agents from prowlr-marketplace repo. One-click install adds agent to Agent Hub.

### 11.2 MCP Server Marketplace
MCP server configurations as installable plugins. Each includes: server config, Docker image reference, tool manifest, setup instructions.

### 11.3 Security Scan Pack
ShipSec's security components (nuclei, subfinder, trufflehog, naabu, httpx, amass, etc.) packaged as a marketplace plugin.

### 11.4 Component Packs
Community-contributed workflow components published to marketplace. SDK (@prowlrbot/component-sdk) for building custom components.

---

## 12. Success Criteria

### Phase 1: Ship Studio (target)
- All 400+ ShipSec references replaced with ProwlrBot branding
- All 4 CRITICAL and 6 HIGH security findings fixed
- Studio starts with `prowlr studio` CLI command
- Agent Hub page shows all installed agents with status
- Agent Workspace shows live browser/terminal/code per agent (requires Docker)
- At minimum Screen, Terminal, Code, Tools, Cost, Logs tabs functional
- Tile and Stack layout modes functional
- ProwlrBot JWT auth working as default provider
- Works with zero optional services (SQLite + filesystem only; Docker for workspaces)
- Collaboration Canvas shows agent findings (read-only)
- 713+ existing ProwlrBot tests still passing

### Phase 2: Full Feature Parity
- All 12 tabs per agent workspace functional
- All 6 layout modes functional
- Chat, Channels, Settings, Monitors, Cron pages rebuilt in Studio
- Collaboration Canvas with editing and export
- Security scan components extracted to marketplace package
- Float, Split, PiP, Focus layout modes

### Phase 3: Console Retirement
- Old console removed from codebase
- Studio is the only frontend
- Migration guide published for users upgrading
