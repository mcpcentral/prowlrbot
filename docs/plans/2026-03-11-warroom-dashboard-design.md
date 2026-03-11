# War Room Dashboard, Statusline & Learning Engine Design

> **Date:** 2026-03-11
> **Status:** Approved
> **Scope:** Interactive war room UI, Claude Code statusline, knowledge indexing, learning engine

---

## 1. Overview

Three interconnected systems that make ProwlrBot's multi-agent coordination visible, intelligent, and polished:

1. **War Room Dashboard** — visual mission control in the console + lightweight bridge status page
2. **Statusline** — always-on connection status in Claude Code terminals
3. **Learning Engine** — agents get smarter over time via automatic observation capture, persistence, and context injection

Design informed by claude-mem's plugin architecture (card-based UI, SQLite + FTS5 + vector DB, hook-driven capture, background worker) and jcodemunch's indexing patterns (Tree-sitter AST, incremental indexing, lazy loading, hash verification).

---

## 2. War Room Dashboard

### 2.1 Console Page (`/warroom` — React + Ant Design)

Lives inside the existing console at port 8088. Consumes the hub bridge REST API and the existing WebSocket infrastructure.

#### Layout

```
┌─────────────────────────────────────────────────────────┐
│  WAR ROOM                    Filter ▾   🟢 5 agents     │
├──────────────┬──────────────┬───────────────────────────┤
│  AGENTS      │  KANBAN      │  LIVE FEED                │
│              │  BOARD       │                            │
│ 🟢 architect │ Pending │ Claimed │ Active │ Done        │
│   python,api │ ┌─────┐ ┌─────┐  ┌─────┐               │
│   idle       │ │ROAR │ │eco- │  │Bug- │  04:28 arch    │
│              │ │spec │ │sys  │  │Claw │    claimed...   │
│ 🔵 test-wiz  │ └─────┘ └─────┘  └─────┘               │
│   python,test│                                          │
│   working    │ Drag-and-drop between columns            │
│              │ Click → slide-out detail panel            │
├──────────────┴──────────────┤                            │
│  SHARED FINDINGS            │  Filterable by event type  │
│  📌 auth-vuln-1    ★ 3     │  Color-coded cards         │
│  📌 api-pattern    ★ 1     │  Sound toggle              │
│  📌 perf-baseline          │  Follow-agent mode         │
├─────────────────────────────┤                            │
│  FILE LOCKS (tree view)     │                            │
│  src/                       │                            │
│  ├── hub/ 🔒 architect      │                            │
│  └── agents/ 🔒 test-wiz   │                            │
└─────────────────────────────┴───────────────────────────┘
```

#### Data Sources (all exist — no new backend)

| Panel | Endpoint | Method |
|-------|----------|--------|
| Agent cards | `GET :8099/agents` | Poll 5s or WebSocket |
| Kanban board | `GET :8099/board` | Poll 5s or WebSocket |
| Live feed | `GET :8099/events` | Poll 3s or WebSocket |
| Shared findings | `GET :8099/context` | Poll 10s |
| File locks | `POST :8099/conflicts` | Poll 5s |

#### Interactive Features

- **Drag-and-drop kanban** — move tasks between Pending → Claimed → In Progress → Done
- **Slide-out task detail panel** — description, file locks, progress notes, event timeline
- **Quick-claim button** — generates `claude mcp` command to paste into any terminal
- **Task creation form** — title, priority, file scopes, required capabilities
- **Filter bar** — by status, priority, agent, capability tag
- **Blocked task visualization** — red dashed borders, dependency arrows
- **Command palette** (Cmd+K / Ctrl+K) — quick actions: claim, broadcast, share finding, lock file

#### Agent Cards

- Live pulse animation on working agents
- Capability tags as colored chips (python=blue, security=red, frontend=green)
- Current task linked — click agent to highlight their task on board
- Heartbeat indicator — green → yellow → red as heartbeat ages
- Expandable timeline — last 10 actions
- Machine/platform badge — macOS / WSL / Linux icon

#### Live Feed

- Filterable by event type (task, lock, broadcast, finding)
- Color-coded slide-in animation cards
- Sound notifications toggle (subtle chime on task completion / broadcast)
- "Follow agent" mode — pin feed to one agent's events
- Expandable payloads — click to see full JSON

#### File Lock Visualization

- Collapsible directory tree of locked files
- Color-coded by agent (unique color per agent)
- Conflict heatmap — frequently locked files glow hotter
- Click file → see lock history (who, when, which task)

#### Shared Findings Wall

- Card grid layout (Pinterest-style)
- Category tags: vulnerability, pattern, decision, blocker, idea
- Star/upvote important findings
- FTS search bar across all findings
- Link findings to tasks

#### Metrics Panel

- Task velocity — tasks completed per hour/day (sparkline)
- Agent utilization — pie chart idle vs working
- Lock contention — conflict frequency
- Session duration — avg task completion time
- Burndown chart — remaining tasks over time
- **Requires:** recharts or lightweight charting library

### 2.2 Bridge Status Page (`http://host:8099/`)

Standalone self-contained HTML served directly by the bridge's FastAPI. No React, no build step. Inspired by claude-mem's `viewer.html` pattern.

#### Features

- ProwlrBot ASCII art header with teal (#14b8a6) accents
- Dark theme (#0a0a0f background) matching console aesthetic
- Agent count + status dots
- Task summary cards (pending/active/done counts)
- Last 10 events with color-coded badges
- Connection health indicator
- **Auto-refresh via AJAX** (no full page reload) every 5 seconds
- **QR code** — scan to open full console warroom on phone
- **Copy bridge URL button** — for sharing with agents
- Fully responsive — works on mobile browsers
- Single HTML file with inline CSS/JS (~200 lines)

### 2.3 WebSocket on Bridge (New)

Currently the bridge is HTTP-only. Add push updates:

- **`/ws/warroom`** WebSocket endpoint on the bridge
- Emits events on every DB mutation (task claimed, agent connected, lock acquired, etc.)
- Console subscribes once → instant UI updates, no polling
- **SSE fallback** (`/events/stream`) for the standalone status page
- Heartbeat pings every 30s (matching existing console WebSocket pattern)

---

## 3. Statusline

### Architecture

```
Claude Code statusline (polls every 5-10s)
    ↓
prowlr-statusline.js (Bun/Node)
    ↓
Direct SQLite read from ~/.prowlrbot/warroom.db
    ↓
Returns JSON: {"agents": 5, "working": 2, "tasks": 7, "locks": 3, "status": "connected"}
    ↓
Claude Code renders: 🐾 5 agents · 2 working · 7 tasks · 🔒3
```

### Design Decisions

- **Direct SQLite read** — no HTTP, no worker, sub-10ms (matching claude-mem's pattern)
- **Project-scoped** — reads the room matching current working directory
- **Graceful fallback** — returns `{"status": "disconnected"}` if DB missing or empty
- **Registered via hooks.json** in the prowlr-hub plugin

### Display Format

```
🐾 ProwlrHub: 5 agents · 2 working · 7 tasks · 🔒3
```

### Enhanced Features

- **Rotating ticker** — cycles through recent events every 10s
- **Alert mode** — highlights if a broadcast targets you or conflict detected
- **Click-to-expand** in supported terminals → shows mini board summary

### Implementation

Single file: `scripts/statusline.js` (~60 lines)
- Opens `warroom.db` read-only
- Counts agents WHERE status != 'disconnected'
- Counts tasks by status
- Counts active file locks
- Returns JSON to stdout

---

## 4. Learning Engine

### 4.1 Architecture

```
Detection Triggers              Storage                      Injection
──────────────────              ───────                      ─────────
User corrects agent  ──┐
Agent retries tool   ──┤       ~/.prowlrbot/
Preference expressed ──┼──►     ├── learnings.db             System Prompt:
Pattern discovered   ──┤       │   ├── observations (FTS5)   "You previously
Task succeeds/fails  ──┘       │   ├── sessions              learned: ..."
                               │   ├── preferences           (token-budgeted,
                               │   └── patterns              decayed by age)
                               ├── embeddings/
                               │   └── chroma/ (vector DB)
                               └── index/
                                   └── (incremental, jcodemunch-style)
```

### 4.2 Database Schema (`learnings.db`)

```sql
-- Core learning observations
CREATE TABLE learnings (
    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    session_id TEXT,
    type TEXT NOT NULL,  -- correction, preference, pattern, failure, success
    trigger TEXT,        -- what caused this learning
    content TEXT NOT NULL,
    context TEXT,        -- surrounding code/conversation context
    confidence REAL DEFAULT 0.5,  -- 0.0-1.0, increases with repetition
    decay_score REAL DEFAULT 1.0, -- decreases over time
    created_at INTEGER NOT NULL,
    last_used_at INTEGER,
    use_count INTEGER DEFAULT 0
);

-- Full-text search
CREATE VIRTUAL TABLE learnings_fts USING fts5(
    content, context, trigger,
    content=learnings, content_rowid=rowid
);

-- User preferences
CREATE TABLE preferences (
    id TEXT PRIMARY KEY,
    project TEXT,
    category TEXT,  -- code_style, tool_usage, communication, workflow
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,    -- explicit (user said), inferred (observed)
    confidence REAL DEFAULT 0.5,
    created_at INTEGER
);

-- Session summaries (like claude-mem)
CREATE TABLE learning_sessions (
    session_id TEXT PRIMARY KEY,
    project TEXT,
    started_at INTEGER,
    completed_at INTEGER,
    learnings_captured INTEGER DEFAULT 0,
    summary TEXT
);
```

### 4.3 Hook Integration

| Hook Event | Action |
|------------|--------|
| `PostToolUse` | Capture tool success/failure, detect retries |
| `Stop` | Summarize session learnings, update confidence scores |
| `SessionStart` | Query relevant learnings, inject into context |
| `UserPromptSubmit` | Detect corrections ("no, I meant..."), preference signals |

### 4.4 Context Injection

On `SessionStart`, the learning engine:

1. Queries learnings for current project (FTS5 + vector similarity)
2. Ranks by `confidence * decay_score * relevance`
3. Budgets to ~500 tokens (configurable)
4. Injects as structured block in system prompt:

```markdown
## Learnings (auto-captured)
- This project uses Black formatter, not Ruff (confidence: 0.9)
- User prefers short commit messages without scope (confidence: 0.7)
- pytest-asyncio requires asyncio_mode = "auto" in this repo (confidence: 1.0)
```

### 4.5 Decay & Compaction

- **Time decay:** `decay_score *= 0.95` daily (unused learnings fade)
- **Usage boost:** Each time a learning is injected and not corrected, `confidence += 0.1`
- **Compaction:** Monthly job merges similar learnings, removes low-confidence ones
- **Manual override:** User can say "forget that" or "always remember X"

### 4.6 Free vs Pro Tiers

| Feature | Free | Pro |
|---------|------|-----|
| Correction capture | 10/session | Unlimited |
| Preference learning | Basic keyword | Pattern recognition |
| Code indexing | Manual `prowlr index` | Auto on file change (fswatch) |
| Vector search | — | Semantic similarity via Chroma |
| Cross-session memory | Last 5 sessions | Full history |
| Decay/compaction | Simple age-based | Smart relevance scoring |
| Learning export | — | JSON/markdown export |

### 4.7 Integration with Graduated Autonomy

| Level | Learning Behavior |
|-------|-------------------|
| Watch | Read-only: observe but don't store |
| Guide | Suggest: "I noticed you prefer X, should I remember that?" |
| Delegate | Auto-learn: capture and apply without asking |
| Autonomous | Full: apply learnings, adjust behavior, self-compact |

---

## 5. Knowledge Indexing (jcodemunch-inspired)

### What We Borrow

| Pattern | Source | Our Use |
|---------|--------|---------|
| Tree-sitter AST parsing | jcodemunch | Structural code understanding for learnings |
| Incremental indexing | jcodemunch | Only re-process changed files |
| Lazy loading | jcodemunch | Outline first, full content on demand |
| Hash verification | jcodemunch | Detect stale index entries |
| FTS5 full-text search | claude-mem | Fast text search across learnings |
| Chroma vector DB | claude-mem | Semantic similarity for context injection |
| Background worker | claude-mem | Non-blocking index updates |

### Index Storage

```
~/.prowlrbot/
├── learnings.db          ← SQLite + FTS5 (learnings, preferences, sessions)
├── embeddings/
│   └── chroma/           ← Vector embeddings for semantic search
└── index/
    └── <project-hash>/   ← Per-project incremental code index
        ├── symbols.db    ← Function/class/method signatures
        ├── outline.json  ← Cached repo structure
        └── checksums     ← File hashes for staleness detection
```

---

## 6. Build Order

| Phase | Component | Effort | Dependencies |
|-------|-----------|--------|-------------|
| 1 | Statusline script | ~1 file, 60 lines | warroom.db exists |
| 2 | Bridge status page | ~1 file, 200 lines HTML | Bridge running |
| 3 | Console `/warroom` page | ~5 files, React components | Console exists |
| 4 | WebSocket on bridge | ~100 lines in bridge.py | Bridge running |
| 5 | Command palette | ~2 files, React component | /warroom page |
| 6 | Metrics panel + recharts | ~3 files | /warroom page |
| 7 | Learning Engine hooks | ~4 files, hook scripts | Plugin hooks.json |
| 8 | Learning DB + FTS5 | ~2 files, schema + queries | SQLite |
| 9 | Context injection | ~1 file, SessionStart hook | Learning DB |
| 10 | Vector embeddings | ~2 files, Chroma integration | API key for embeddings |
| 11 | Code indexing | ~3 files, incremental indexer | Tree-sitter |
| 12 | Mobile responsive + PWA | CSS + manifest | /warroom page |

---

## 7. Tech Stack Additions

| Component | Library | Why |
|-----------|---------|-----|
| Kanban drag-and-drop | `@hello-pangea/dnd` or `dnd-kit` | Lightweight, React 18 compatible |
| Charts | `recharts` | Composable, lightweight, good dark theme support |
| WebSocket (bridge) | FastAPI native WebSocket | Already used in main app |
| SSE (bridge status) | Starlette `EventSourceResponse` | Lightweight push for standalone page |
| Vector DB | ChromaDB | Same as claude-mem, proven pattern |
| AST parsing | `tree-sitter` Python bindings | Same as jcodemunch, structural code understanding |
| FTS5 | SQLite built-in | No additional dependency |

---

## 8. Success Criteria

- [ ] Statusline shows agent/task counts in Claude Code terminal within 10ms
- [ ] Bridge status page loads at `http://host:8099/` without React build
- [ ] Console `/warroom` renders kanban board with real-time updates
- [ ] Drag-and-drop task management works
- [ ] Agent cards show live status with pulse animation
- [ ] Command palette opens with Cmd+K
- [ ] Learning Engine captures corrections automatically via PostToolUse hook
- [ ] Learnings inject into SessionStart context (token-budgeted)
- [ ] Free tier works without API key (no vector search)
- [ ] All dark theme with ProwlrBot brand colors (#0a0a0f, #14b8a6)
