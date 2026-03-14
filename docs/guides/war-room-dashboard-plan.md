# War Room Dashboard — Brainstorm & Plan

You want a **more interactive** dashboard: click on agents, see their steps or thinking, feel like they’re “talking to each other.” Here’s what exists today and concrete ideas to get there.

---

**Implementation (React console):** Phases 1–5 and ROAR are implemented in the console War Room page: live WebSocket merge, broadcast speech bubbles, agent drill-down drawer, task timeline in task drawer, filters in Live Feed, and ROAR stream panel (SSE when backend exposes `/roar/events`). See `console/src/pages/WarRoom/`.

## What you have today

| Data | Where | What it is |
|------|--------|-------------|
| **Agents** | `GET /agents`, `GET /api/agents` | Name, status (idle/working/disconnected), capabilities, `current_task_id` |
| **Tasks** | `GET /board`, `GET /api/board` | Title, description, status, priority, owner, **progress_note** (single “what I’m doing now”) |
| **Events** | `GET /events`, `GET /api/events` | Type, agent_id, task_id, payload, timestamp. Types: `agent.connected`, `task.claimed`, `task.updated`, `task.completed`, `agent.broadcast`, `finding.shared`, `lock.acquired`, etc. |
| **Shared context** | `GET /context`, `GET /api/context` | Key/value findings agents shared with the room |
| **Real-time** | `WS /ws/warroom` | Every engine mutation is pushed as a JSON event to all connected clients |

The current status page is **polling** every 5s and shows: stats (agents/tasks/room), agent list, recent events. No drill-down, no live updates, no “conversation” feel.

---

## Ideas for “interactive” and “agents talking”

### 1. **Live feed (war room log)**

- **One scrollable stream** of everything that happens, newest first.
- Use **WebSocket** so new events appear instantly (no 5s refresh).
- Each row: time, event type badge, agent name (if any), short description from payload.
- **Click a row** → expand to show full payload (message, progress_note, task title, etc.).
- Filter by type: e.g. “Only broadcasts” or “Only task events.”

This gives the “everyone in the same room” feeling and is the best place to see agents “talking” (broadcasts) and acting (claims, updates, completions).

### 2. **Broadcasts as “agents talking”**

- **agent.broadcast** events are the main “speech”: an agent sends a `message` to the room.
- In the UI, treat these like **chat bubbles**: agent avatar/name + message, maybe a distinct color per agent.
- Optionally a **dedicated “Broadcasts”** panel or filter so you can read only what agents said, in order.

No backend change; just how you render `event.type === 'agent.broadcast'` and `payload.message`.

### 3. **Click an agent → “Agent detail”**

- From the agents list, **click an agent** → side panel or modal with:
  - **Current task** (if any): title, description, **progress_note** (this is the closest to “current step” today).
  - **This agent’s timeline**: events where `agent_id === this agent` (claimed, updated, completed, broadcast, shared finding).
- So you see “what this agent is doing and what they did recently.”

All data is already in `/api/events` and `/api/board`; filter client-side by `agent_id` and optionally by `task_id`.

### 4. **Click a task → “Task detail”**

- From the mission board, **click a task** → panel with:
  - Full task: title, description, status, priority, owner, **progress_note**.
  - **Task timeline**: events for this `task_id` (created, claimed by X, updated: “note”, completed/failed).
- Reads as “steps” for that task: claim → updates (progress notes) → done/fail.

Again, filter `/api/events` by `task_id`; no new API.

### 5. **Unified “conversation” view**

- Same live feed as (1), but **render by type** so it feels like one thread:
  - **Broadcast** → “**Agent A**: message”
  - **task.claimed** → “**Agent B** picked up *Task title*”
  - **task.updated** → “**Agent B** (on *Task*): progress_note”
  - **finding.shared** → “**Agent A** shared **key**: value”
- Optional filter: “Only broadcasts + findings” = “what agents said and shared.”

### 6. **“Steps” and “thinking” without backend changes**

- **Steps**: Use **events** for a task: claim → one or more `task.updated` (progress_note) → complete/fail. The “steps” are the ordered list of those events; the progress_notes are the step descriptions.
- **Thinking**: The closest today is **broadcasts** (“I’m investigating X”) and **progress_note** (“Added tests, about to refactor”). Expose both clearly in the agent and task drill-downs and in the live feed.

If you later want a dedicated “steps” or “thinking” table (e.g. multiple steps per task with timestamps), that would be a small schema/API addition; the above works with current data.

---

## Suggested build order

| Phase | What | Why first |
|-------|------|-----------|
| **1** | **WebSocket + live event feed** | Real-time beats polling; one feed is the backbone for everything else. |
| **2** | **Better event rendering** | Broadcasts as “speech”, task events as short sentences (e.g. “X claimed Y”, “X: note”). Makes the feed feel like “agents talking and acting.” |
| **3** | **Agent drill-down** | Click agent → current task + agent’s event timeline. Delivers “see this agent’s steps.” |
| **4** | **Task drill-down** | Click task → task detail + task event timeline. Delivers “see steps for this task.” |
| **5** | **Filters / tabs** | “All” / “Broadcasts” / “Task events” / “Findings” so you can focus. |

---

## Tech choices for the new dashboard

- **Option A — Single HTML + JS (like current status page)**  
  One big HTML with CSS/JS, fetch `/api/*`, connect to `ws://.../ws/warroom`, render feed + agent list + board; add modals/panels for agent and task detail. Fits the bridge’s “no build” setup; good for a first iteration.

- **Option B — Small app (e.g. React/Vue/Svelte)**  
  If you prefer components and state management, build a small app that talks to the same REST + WebSocket APIs; host it next to the bridge or from the console. Same backend, richer UI.

- **Option C — Integrate into main ProwlrBot console**  
  If the main app already has a “War Room” or “Hub” section, add this dashboard there (same APIs, possibly same WebSocket from the app’s backend proxy). Keeps one place to “watch” the war room.

---

## Summary

- **“Agents talking”** = broadcasts + shared findings, rendered prominently (e.g. chat-like or as a dedicated feed).
- **“See their steps / thinking”** = agent timeline (events for that agent) + task timeline (events for that task) + **progress_note** and **broadcast** messages.
- **More interactive** = live WebSocket feed + clickable agents and tasks with detail panels.
- You can do all of this with **existing APIs and WebSocket**; no backend changes required for the first version. If you want, next step is a concrete UI spec (wireframes or component list) for Phase 1–2.
