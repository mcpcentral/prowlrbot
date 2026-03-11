# War Room Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an interactive war room dashboard (console + bridge), Claude Code statusline, and learning engine foundations.

**Architecture:** The console gets a full `/warroom` React page with kanban board, agent cards, live feed, and metrics — consuming the existing hub bridge REST API. The bridge serves a standalone HTML status page at its root. A statusline script reads SQLite directly for sub-10ms terminal status. Learning engine hooks capture observations via PostToolUse.

**Tech Stack:** React 18, TypeScript, Ant Design, recharts, @hello-pangea/dnd (kanban), FastAPI WebSocket, SQLite + FTS5, Node statusline script.

**Security Notes:**
- Bridge status page uses safe DOM methods (createElement, textContent) — no innerHTML with untrusted data
- All bridge API endpoints validate input via Pydantic BaseModel
- WebSocket connections use ping/pong keepalive, dead client cleanup
- Learning DB uses parameterized queries (no SQL injection)
- CORS on bridge API limited to console origin

---

### Task 1: Install Console Dependencies

**Files:**
- Modify: `console/package.json`

**Step 1: Add kanban and charting libraries**

```bash
cd console && npm install recharts @hello-pangea/dnd
```

**Step 2: Verify installation**

```bash
cd console && npm ls recharts @hello-pangea/dnd
```

Expected: Both packages listed without errors.

**Step 3: Commit**

```bash
git add console/package.json console/package-lock.json
git commit -m "chore(console): add recharts and dnd-kit for war room dashboard"
```

---

### Task 2: Statusline Script

**Files:**
- Create: `plugins/prowlr-hub/scripts/statusline.js`
- Modify: `plugins/prowlr-hub/hooks/hooks.json`

**Step 1: Create the statusline script**

Create `plugins/prowlr-hub/scripts/statusline.js` — a lightweight Node script that:
- Opens `~/.prowlrbot/warroom.db` read-only using `node:sqlite` DatabaseSync
- Counts agents (non-disconnected), working agents, tasks, and active file locks
- Returns JSON: `{"agents":5,"working":2,"tasks":7,"locks":3,"status":"connected"}`
- Falls back to `{"status":"disconnected"}` if DB missing
- Falls back to `{"status":"error"}` on any exception
- Target: sub-10ms execution

**Step 2: Update hooks.json to register statusline**

Add a `Notification` hook with matcher `statusline` that runs the script with 5s timeout.

**Step 3: Test**

```bash
PROWLR_HUB_DB=~/.prowlrbot/warroom.db node plugins/prowlr-hub/scripts/statusline.js
```

Expected: JSON with agent/task counts.

**Step 4: Commit**

```bash
git add plugins/prowlr-hub/scripts/statusline.js plugins/prowlr-hub/hooks/hooks.json
git commit -m "feat(hub): add statusline script for Claude Code terminal status"
```

---

### Task 3: Bridge Status Page (Standalone HTML)

**Files:**
- Create: `src/prowlrbot/hub/status_page.py`
- Modify: `src/prowlrbot/hub/bridge.py`

**Step 1: Create status_page.py**

A Python module containing `STATUS_HTML` — a self-contained HTML page with:
- Dark theme (#0a0a0f bg, #14b8a6 teal accents) matching ProwlrBot brand
- Stats cards grid (agents, tasks, room status)
- Agent list with status dots and capability tags
- Recent events list with timestamps and type badges
- Auto-refresh every 5s via fetch + safe DOM manipulation (createElement/textContent, NO innerHTML with untrusted data)
- Responsive layout (mobile-friendly)
- ProwlrBot branding and footer

**SECURITY:** All dynamic content rendered using `document.createElement()` and `textContent`. No `innerHTML` with server data.

**Step 2: Add root route to bridge.py**

Import `HTMLResponse` from fastapi.responses and `STATUS_HTML` from status_page. Add `GET /` route returning the HTML.

**Step 3: Verify**

```bash
PYTHONPATH=src python3 -m prowlrbot.hub.bridge &
sleep 2 && curl -s http://localhost:8099/ | head -5 && kill %1
```

**Step 4: Commit**

```bash
git add src/prowlrbot/hub/status_page.py src/prowlrbot/hub/bridge.py
git commit -m "feat(hub): add standalone HTML status page at bridge root"
```

---

### Task 4: Bridge JSON API Endpoints

**Files:**
- Modify: `src/prowlrbot/hub/bridge.py`

**Step 1: Check existing endpoints**

Inspect whether `/agents`, `/board`, `/events` return JSON-serializable dicts or formatted strings.

**Step 2: Add `/api/` JSON endpoints**

Add these endpoints returning raw JSON arrays/dicts from the engine:
- `GET /api/agents` — list of agent dicts
- `GET /api/board?status=` — list of task dicts
- `GET /api/events?limit=50&event_type=` — list of event dicts
- `GET /api/context?key=` — list of finding dicts
- `GET /api/conflicts` — list of active file lock dicts

**Step 3: Add CORS middleware**

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8088"], allow_methods=["*"], allow_headers=["*"])
```

**Step 4: Test**

```bash
curl -s http://localhost:8099/api/agents | python3 -m json.tool | head -20
```

**Step 5: Commit**

```bash
git add src/prowlrbot/hub/bridge.py
git commit -m "feat(hub): add JSON API endpoints and CORS for dashboard"
```

---

### Task 5: Bridge WebSocket

**Files:**
- Modify: `src/prowlrbot/hub/bridge.py`
- Modify: `src/prowlrbot/hub/engine.py`

**Step 1: Add WebSocket endpoint**

Add `/ws/warroom` WebSocket endpoint to bridge.py:
- Module-level `_ws_clients: set[WebSocket]` for connected clients
- `broadcast_ws(event)` function to push to all clients
- Ping/pong keepalive every 30s
- Dead client cleanup on disconnect

**Step 2: Add event callback to engine**

Add `set_event_callback()` and `_notify()` to WarRoomEngine. Call `_notify()` after each mutation (claim, complete, fail, register, lock, unlock, broadcast, share_finding).

Wire the callback in bridge.py to call `broadcast_ws()`.

**Step 3: Test**

```bash
python3 -c "
import asyncio, websockets
async def test():
    async with websockets.connect('ws://localhost:8099/ws/warroom') as ws:
        await ws.send('ping')
        print(await ws.recv())
asyncio.run(test())
"
```

Expected: `pong`

**Step 4: Commit**

```bash
git add src/prowlrbot/hub/bridge.py src/prowlrbot/hub/engine.py
git commit -m "feat(hub): add WebSocket push for real-time dashboard updates"
```

---

### Task 6: Console War Room API Client

**Files:**
- Create: `console/src/api/warroom.ts`

**Step 1: Create API client**

TypeScript module with:
- `BRIDGE_URL` from env or default `http://localhost:8099`
- Type interfaces: `Agent`, `Task`, `WarRoomEvent`, `Finding`
- Fetch functions: `warroom.agents()`, `warroom.board()`, `warroom.events()`, `warroom.context()`, `warroom.conflicts()`
- `connectWarRoomWS()` — returns cleanup function, auto-reconnects on disconnect, 25s keepalive pings

**Step 2: Commit**

```bash
git add console/src/api/warroom.ts
git commit -m "feat(console): add war room API client and WebSocket connector"
```

---

### Task 7: Kanban Board Component

**Files:**
- Create: `console/src/pages/WarRoom/KanbanBoard.tsx`
- Create: `console/src/pages/WarRoom/KanbanBoard.module.less`

**Step 1: Build KanbanBoard component**

4-column drag-and-drop kanban (Pending, Claimed, In Progress, Done) using `@hello-pangea/dnd`.

Each task card shows:
- Priority color bar (left border: high=red, normal=blue, low=gray)
- Title
- Owner tag (if claimed)
- File scope count badge
- Blocked indicator (red dashed border if `blocked_by.length > 0`)
- Progress note preview (truncated to 1 line)

Props: `tasks: Task[]`, `onTaskSelect: (task: Task) => void`, `onTaskMove: (taskId: string, newStatus: string) => void`

**Step 2: Styles**

Dark theme matching brand. Columns flex row with scroll. Cards with hover lift effect and grab cursor. Dragging state with teal glow shadow.

**Step 3: Commit**

```bash
git add console/src/pages/WarRoom/KanbanBoard.tsx console/src/pages/WarRoom/KanbanBoard.module.less
git commit -m "feat(console): add kanban board with drag-and-drop"
```

---

### Task 8: Agent Cards Component

**Files:**
- Create: `console/src/pages/WarRoom/AgentCards.tsx`
- Create: `console/src/pages/WarRoom/AgentCards.module.less`

**Step 1: Build AgentCards component**

CSS Grid of agent cards. Each card:
- Status dot with pulse animation (green=idle, blue=working, gray=disconnected)
- Agent name (bold)
- Capability tags as colored chips
- Current task title (if working, linked to kanban card)
- Heartbeat age: `< 1min` green, `< 3min` yellow, `> 5min` red
- Platform badge: macOS/Linux/WSL icon

Props: `agents: Agent[]`, `onAgentSelect: (agent: Agent) => void`

**Step 2: Commit**

```bash
git add console/src/pages/WarRoom/AgentCards.tsx console/src/pages/WarRoom/AgentCards.module.less
git commit -m "feat(console): add agent cards with status indicators"
```

---

### Task 9: Live Feed & Findings Wall

**Files:**
- Create: `console/src/pages/WarRoom/LiveFeed.tsx`
- Create: `console/src/pages/WarRoom/FindingsWall.tsx`

**Step 1: Build LiveFeed**

Scrollable event list:
- Filter tabs: All | Tasks | Locks | Broadcasts
- Event card: timestamp, type badge (colored by category), agent name, description
- Slide-in animation (CSS keyframes) for new events
- Max 100 events, newest first
- "Follow agent" dropdown filter

**Step 2: Build FindingsWall**

Card grid of shared findings:
- Key as title, value as content, agent name, timestamp
- Search input with FTS filtering
- Expandable cards (click to see full value)

**Step 3: Commit**

```bash
git add console/src/pages/WarRoom/LiveFeed.tsx console/src/pages/WarRoom/FindingsWall.tsx
git commit -m "feat(console): add live feed and findings wall"
```

---

### Task 10: War Room Page Assembly + Routing

**Files:**
- Create: `console/src/pages/WarRoom/index.tsx`
- Create: `console/src/pages/WarRoom/WarRoom.module.less`
- Modify: `console/src/layouts/MainLayout/index.tsx`
- Modify: `console/src/layouts/Sidebar.tsx`

**Step 1: Create main page**

`console/src/pages/WarRoom/index.tsx`:
- Polls bridge API every 5s (agents, board, events, context, conflicts)
- Connects WebSocket for live push (merges into event list)
- Layout: header bar → agents row → kanban + feed columns → findings + metrics
- Task detail Drawer (Ant Design) opens when clicking a kanban card
- Connection status indicator in header

**Step 2: Create WarRoom.module.less**

Master layout: CSS Grid with responsive breakpoints. Dark theme. Smooth transitions on data updates.

**Step 3: Add route**

In `MainLayout/index.tsx`:
- Import `WarRoomPage`
- Add `"/warroom": "warroom"` to `pathToKey`
- Add `<Route path="/warroom" element={<WarRoomPage />} />`

**Step 4: Add sidebar nav**

In `Sidebar.tsx`:
- Import `Swords` from lucide-react
- Add `warroom: "/warroom"` to `keyToPath`
- Add menu item after dashboard: `{ key: "warroom", label: "War Room", icon: <Swords size={16} /> }`

**Step 5: Build and verify**

```bash
cd console && npm run build
```

Expected: No TypeScript errors, build succeeds.

**Step 6: Commit**

```bash
git add console/src/pages/WarRoom/ console/src/layouts/MainLayout/index.tsx console/src/layouts/Sidebar.tsx
git commit -m "feat(console): assemble /warroom page with routing and nav"
```

---

### Task 11: Metrics Panel

**Files:**
- Create: `console/src/pages/WarRoom/MetricsPanel.tsx`
- Modify: `console/src/pages/WarRoom/index.tsx`

**Step 1: Build MetricsPanel**

Uses recharts:
- Task velocity `<AreaChart>` — tasks completed per hour (from events)
- Agent utilization `<PieChart>` — idle/working/disconnected
- Lock contention `<BarChart>` — lock events per hour

Collapsible section with "Metrics" header.

**Step 2: Integrate into main page**

Add MetricsPanel below kanban in WarRoom/index.tsx.

**Step 3: Build and verify**

```bash
cd console && npm run build
```

**Step 4: Commit**

```bash
git add console/src/pages/WarRoom/MetricsPanel.tsx console/src/pages/WarRoom/index.tsx
git commit -m "feat(console): add metrics panel with recharts"
```

---

### Task 12: Learning Engine Database

**Files:**
- Create: `src/prowlrbot/learning/__init__.py`
- Create: `src/prowlrbot/learning/db.py`

**Step 1: Create learning module**

`src/prowlrbot/learning/db.py`:
- `init_db(path)` — creates SQLite DB with WAL mode, tables: learnings (with FTS5), preferences, learning_sessions
- `add_learning(conn, project, type, content, ...)` — insert with UUID id
- `query_learnings(conn, project, limit)` — ranked by `confidence * decay_score`
- `search_learnings(conn, query, limit)` — FTS5 search
- All queries use parameterized statements (no SQL injection)

**Step 2: Test**

```bash
PYTHONPATH=src python3 -c "
from prowlrbot.learning.db import init_db, add_learning, query_learnings
conn = init_db('/tmp/test_learnings.db')
lid = add_learning(conn, 'test', 'correction', 'Use Black formatter')
results = query_learnings(conn, 'test')
print(f'Created {lid}, found {len(results)} learnings')
conn.close()
import os; os.remove('/tmp/test_learnings.db')
"
```

Expected: `Created learn-..., found 1 learnings`

**Step 3: Commit**

```bash
git add src/prowlrbot/learning/
git commit -m "feat(learning): add learning engine database with SQLite + FTS5"
```

---

### Task 13: Learning Engine Hooks

**Files:**
- Create: `plugins/prowlr-hub/hooks/scripts/capture-learning.sh`
- Modify: `plugins/prowlr-hub/hooks/hooks.json`

**Step 1: Create capture hook**

Shell script that runs on PostToolUse for Edit/Write/Bash. On tool failure (non-zero exit), records a "failure" learning via Python. Uses parameterized SQL (calls `add_learning()` function, not raw SQL).

**Step 2: Update hooks.json**

Add PostToolUse hook with matcher `Edit|Write|MultiEdit|Bash`, 10s timeout.

**Step 3: Commit**

```bash
git add plugins/prowlr-hub/hooks/scripts/capture-learning.sh plugins/prowlr-hub/hooks/hooks.json
git commit -m "feat(learning): add PostToolUse hook for automatic learning capture"
```

---

### Task 14: Integration Test & Final Build

**Files:**
- Rebuild: `console/dist/`

**Step 1: Full console build**

```bash
cd console && npm run build
```

Expected: Build succeeds.

**Step 2: Verify bridge status page**

```bash
PYTHONPATH=src python3 -m prowlrbot.hub.bridge &
sleep 2
curl -s http://localhost:8099/ | grep "PROWLRHUB" && echo "✓ Status page"
curl -s http://localhost:8099/api/agents | python3 -c "import json,sys; print(f'✓ {len(json.load(sys.stdin))} agents')"
kill %1
```

**Step 3: Verify statusline**

```bash
node plugins/prowlr-hub/scripts/statusline.js && echo "✓ Statusline"
```

**Step 4: Verify learning DB**

```bash
PYTHONPATH=src python3 -c "
from prowlrbot.learning.db import init_db
conn = init_db('/tmp/verify.db')
print('✓ Learning DB schema valid')
conn.close()
import os; os.remove('/tmp/verify.db')
"
```

**Step 5: Commit build**

```bash
git add console/dist/
git commit -m "build(console): rebuild with war room dashboard and metrics"
```

---

### Summary

| # | Component | Files | Commits |
|---|-----------|-------|---------|
| 1 | Dependencies | package.json | 1 |
| 2 | Statusline | statusline.js, hooks.json | 1 |
| 3 | Bridge status page | status_page.py, bridge.py | 1 |
| 4 | Bridge JSON API | bridge.py | 1 |
| 5 | Bridge WebSocket | bridge.py, engine.py | 1 |
| 6 | Console API client | warroom.ts | 1 |
| 7 | Kanban board | KanbanBoard.tsx | 1 |
| 8 | Agent cards | AgentCards.tsx | 1 |
| 9 | Live feed + findings | LiveFeed.tsx, FindingsWall.tsx | 1 |
| 10 | Page assembly | index.tsx, MainLayout, Sidebar | 1 |
| 11 | Metrics panel | MetricsPanel.tsx | 1 |
| 12 | Learning DB | learning/db.py | 1 |
| 13 | Learning hooks | capture-learning.sh | 1 |
| 14 | Integration test | console/dist/ | 1 |

**Total: 14 tasks, 14 commits, ~25 files**
