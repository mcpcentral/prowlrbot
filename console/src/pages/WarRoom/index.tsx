import { useEffect, useState, useCallback, useRef } from "react";
import { Drawer } from "antd";
import { warroom, connectWarRoomWS } from "../../api/warroom";
import type { Agent, Task, WarRoomEvent, Finding, FileLock } from "../../api/warroom";
import KanbanBoard from "./KanbanBoard";
import AgentCards from "./AgentCards";
import LiveFeed from "./LiveFeed";
import FindingsWall from "./FindingsWall";
import MetricsPanel from "./MetricsPanel";

function TaskDetailDrawer({
  task,
  onClose,
}: {
  task: Task | null;
  onClose: () => void;
}) {
  if (!task) return null;

  return (
    <Drawer
      title={task.title}
      open={!!task}
      onClose={onClose}
      width={420}
      styles={{
        header: { background: "var(--pb-wr-bg-panel)", borderBottom: "1px solid var(--pb-wr-border)", color: "var(--pb-wr-text)" },
        body: { background: "var(--pb-wr-bg-deep)", color: "var(--pb-wr-text)" },
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11, textTransform: "uppercase", marginBottom: 4 }}>
            Status
          </div>
          <span
            style={{
              padding: "2px 8px",
              borderRadius: 4,
              fontSize: 12,
              background:
                task.status === "done"
                  ? "var(--pb-wr-status-done-bg)"
                  : task.status === "failed"
                    ? "var(--pb-wr-status-failed-bg)"
                    : task.status === "in_progress"
                      ? "var(--pb-wr-status-progress-bg)"
                      : "var(--pb-wr-status-pending-bg)",
              color:
                task.status === "done"
                  ? "var(--pb-wr-status-done)"
                  : task.status === "failed"
                    ? "var(--pb-wr-status-failed)"
                    : task.status === "in_progress"
                      ? "var(--pb-wr-status-progress)"
                      : "var(--pb-wr-accent)",
            }}
          >
            {task.status}
          </span>
          <span
            style={{
              marginLeft: 8,
              padding: "2px 8px",
              borderRadius: 4,
              fontSize: 12,
              background:
                task.priority === "high" || task.priority === "critical"
                  ? "var(--pb-wr-priority-high-bg)"
                  : "var(--pb-wr-border)",
              color:
                task.priority === "high" || task.priority === "critical"
                  ? "var(--pb-wr-priority-high)"
                  : "var(--pb-wr-text-secondary)",
            }}
          >
            {task.priority}
          </span>
        </div>

        {task.description && (
          <div>
            <div style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11, textTransform: "uppercase", marginBottom: 4 }}>
              Description
            </div>
            <div style={{ fontSize: 13, color: "var(--pb-wr-text)", lineHeight: 1.5 }}>
              {task.description}
            </div>
          </div>
        )}

        {task.owner_name && (
          <div>
            <div style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11, textTransform: "uppercase", marginBottom: 4 }}>
              Owner
            </div>
            <div style={{ fontSize: 13, color: "var(--pb-wr-accent)" }}>
              {task.owner_name}
            </div>
          </div>
        )}

        {task.file_scopes.length > 0 && (
          <div>
            <div style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11, textTransform: "uppercase", marginBottom: 4 }}>
              File Scopes
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {task.file_scopes.map((f) => (
                <code
                  key={f}
                  style={{
                    fontSize: 11,
                    color: "var(--pb-accent-purple)",
                    background: "var(--pb-wr-border)",
                    padding: "2px 6px",
                    borderRadius: 3,
                  }}
                >
                  {f}
                </code>
              ))}
            </div>
          </div>
        )}

        {task.blocked_by.length > 0 && (
          <div>
            <div style={{ color: "var(--pb-wr-status-failed)", fontSize: 11, textTransform: "uppercase", marginBottom: 4 }}>
              Blocked By
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {task.blocked_by.map((b) => (
                <span key={b} style={{ fontSize: 12, color: "var(--pb-wr-status-failed)" }}>
                  {b}
                </span>
              ))}
            </div>
          </div>
        )}

        {task.progress_note && (
          <div>
            <div style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11, textTransform: "uppercase", marginBottom: 4 }}>
              Progress Note
            </div>
            <div
              style={{
                fontSize: 12,
                color: "var(--pb-wr-text-secondary)",
                background: "var(--pb-wr-bg-card)",
                padding: 8,
                borderRadius: 4,
                whiteSpace: "pre-wrap",
              }}
            >
              {task.progress_note}
            </div>
          </div>
        )}

        <div style={{ display: "flex", gap: 16, fontSize: 11, color: "var(--pb-wr-text-tertiary)", flexWrap: "wrap" }}>
          {task.created_at && (
            <span>Created: {new Date(task.created_at).toLocaleString()}</span>
          )}
          {task.claimed_at && (
            <span>Claimed: {new Date(task.claimed_at).toLocaleString()}</span>
          )}
          {task.completed_at && (
            <span>
              Completed: {new Date(task.completed_at).toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </Drawer>
  );
}

export default function WarRoomPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<WarRoomEvent[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [conflicts, setConflicts] = useState<FileLock[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [a, t, e, f, c] = await Promise.all([
        warroom.agents(),
        warroom.board(),
        warroom.events(100),
        warroom.context(),
        warroom.conflicts(),
      ]);
      setAgents(a);
      setTasks(t);
      setEvents(e);
      setFindings(f);
      setConflicts(c);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    }
  }, []);

  useEffect(() => {
    refresh();

    // WebSocket for real-time updates
    const disconnect = connectWarRoomWS(
      () => {
        // On any event, refresh all data
        refresh();
      },
      (status) => setConnected(status),
    );

    // Fallback polling every 10s
    pollRef.current = setInterval(refresh, 10000);

    return () => {
      disconnect();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [refresh]);

  const handleTaskSelect = useCallback((task: Task) => {
    setSelectedTask(task);
  }, []);

  return (
    <div style={{ padding: 24, background: "var(--pb-wr-bg-deep)", minHeight: "100%" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <div>
          <h1
            style={{
              color: "var(--pb-wr-text)",
              fontSize: 22,
              fontWeight: 700,
              margin: 0,
              letterSpacing: 1,
            }}
          >
            War Room
          </h1>
          <div style={{ color: "var(--pb-wr-text-tertiary)", fontSize: 12, marginTop: 2 }}>
            Multi-agent coordination dashboard
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {error && (
            <span style={{ color: "var(--pb-wr-status-failed)", fontSize: 11 }}>{error}</span>
          )}
          <span
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 11,
              color: connected ? "var(--pb-wr-status-done)" : "var(--pb-wr-status-failed)",
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: connected ? "var(--pb-wr-status-done)" : "var(--pb-wr-status-failed)",
                boxShadow: connected ? "0 0 8px var(--pb-wr-status-done)" : "none",
              }}
            />
            {connected ? "Live" : "Polling"}
          </span>
          <span style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11 }}>
            {agents.filter((a) => a.status !== "disconnected").length} agents |{" "}
            {tasks.length} tasks
          </span>
        </div>
      </div>

      {/* Agent Cards */}
      <div style={{ marginBottom: 16 }}>
        <AgentCards agents={agents} tasks={tasks} />
      </div>

      {/* Metrics */}
      <div style={{ marginBottom: 16 }}>
        <MetricsPanel agents={agents} tasks={tasks} events={events} conflicts={conflicts} />
      </div>

      {/* Kanban Board */}
      <div style={{ marginBottom: 16 }}>
        <KanbanBoard tasks={tasks} onTaskSelect={handleTaskSelect} />
      </div>

      {/* Bottom row: Live Feed + Findings */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <LiveFeed events={events} agents={agents} />
        <FindingsWall findings={findings} agents={agents} />
      </div>

      {/* Task Detail Drawer */}
      <TaskDetailDrawer
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
      />
    </div>
  );
}
