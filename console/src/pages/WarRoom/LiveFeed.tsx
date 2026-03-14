import { useMemo, useState } from "react";
import { Tag } from "antd";
import type { Agent, WarRoomEvent } from "../../api/warroom";
import styles from "./LiveFeed.module.less";

interface LiveFeedProps {
  events: WarRoomEvent[];
  agents?: Agent[];
}

const EVENT_COLORS: Record<string, string> = {
  "task.created": "blue",
  "task.claimed": "cyan",
  "task.updated": "geekblue",
  "task.completed": "green",
  "task.failed": "red",
  "agent.connected": "lime",
  "agent.disconnected": "default",
  "agent.broadcast": "purple",
  "lock.acquired": "orange",
  "lock.released": "default",
  "finding.shared": "gold",
  "conflict.detected": "volcano",
};

const FILTERS = [
  { key: "all", label: "All" },
  { key: "tasks", label: "Tasks" },
  { key: "locks", label: "Locks" },
  { key: "broadcasts", label: "Broadcasts" },
  { key: "findings", label: "Findings" },
] as const;

function matchesFilter(event: WarRoomEvent, filter: string): boolean {
  if (filter === "all") return true;
  if (filter === "tasks") return event.type.startsWith("task.");
  if (filter === "locks")
    return (
      event.type.startsWith("lock.") || event.type.startsWith("conflict.")
    );
  if (filter === "broadcasts") return event.type === "agent.broadcast";
  if (filter === "findings") return event.type === "finding.shared";
  return true;
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "--:--";
  }
}

function EventRow({
  event,
  agentLabel,
  desc,
  isBroadcast,
  tagColor,
  formatTime: fmt,
}: {
  event: WarRoomEvent;
  agentLabel: string;
  desc: string;
  isBroadcast: boolean;
  tagColor: string;
  formatTime: (ts: string) => string;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasPayload = Object.keys(event.payload || {}).length > 0;

  if (isBroadcast && (event.payload?.message || desc)) {
    return (
      <div
        className={styles.broadcastBubble}
        onClick={() => setExpanded((e) => !e)}
      >
        <div className={styles.broadcastHeader}>
          <span className={styles.broadcastTime}>{fmt(event.timestamp)}</span>
          <span className={styles.broadcastAgent}>{agentLabel}</span>
        </div>
        <div className={styles.broadcastMessage}>
          {String(event.payload?.message ?? desc)}
        </div>
        {expanded && hasPayload && (
          <pre className={styles.broadcastPayload}>
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  return (
    <div className={styles.eventRowWrap}>
      <div
        className={styles.eventRow}
        onClick={() => hasPayload && setExpanded((e) => !e)}
      >
        <span className={styles.eventTime}>{fmt(event.timestamp)}</span>
        <Tag color={tagColor} style={{ fontSize: 10, margin: 0 }}>
          {event.type.split(".").pop()}
        </Tag>
        <span className={styles.eventAgent}>
          {agentLabel}
          {event.task_id ? ` \u2192 ${event.task_id.slice(0, 12)}` : ""}
        </span>
        {desc && (
          <span className={styles.eventPayload} title={desc}>
            {desc}
          </span>
        )}
      </div>
      {expanded && hasPayload && (
        <div className={styles.eventPayloadExpand}>
          <pre>{JSON.stringify(event.payload, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function extractDescription(event: WarRoomEvent): string {
  const payload = event.payload;
  if (payload?.message) return String(payload.message);
  if (payload?.title) return String(payload.title);
  if (payload?.key) return `shared: ${String(payload.key)}`;
  if (payload?.file_path) return String(payload.file_path);
  if (payload?.status) return `status: ${String(payload.status)}`;
  return "";
}

export default function LiveFeed({ events, agents }: LiveFeedProps) {
  const [filter, setFilter] = useState<string>("all");
  const [agentFilter, setAgentFilter] = useState<string>("all");

  // Get unique agent IDs from events for the agent filter dropdown
  const agentIds = useMemo(() => {
    const ids = new Set<string>();
    for (const e of events) {
      if (e.agent_id) ids.add(e.agent_id);
    }
    return Array.from(ids).sort();
  }, [events]);

  // Build agent name lookup
  const agentNames = useMemo(() => {
    const map = new Map<string, string>();
    if (agents) {
      for (const a of agents) {
        map.set(a.agent_id, a.name);
      }
    }
    return map;
  }, [agents]);

  const filtered = useMemo(() => {
    return events
      .filter((e) => matchesFilter(e, filter))
      .filter(
        (e) => agentFilter === "all" || e.agent_id === agentFilter,
      )
      .slice(0, 100);
  }, [events, filter, agentFilter]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.title}>Live Feed</span>
        <div className={styles.controls}>
          <div className={styles.filters}>
            {FILTERS.map((f) => (
              <span
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`${styles.filterTab} ${
                  filter === f.key ? styles.filterTabActive : ""
                }`}
              >
                {f.label}
              </span>
            ))}
          </div>
          {agentIds.length > 0 && (
            <select
              className={styles.agentFilter}
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              title="Filter by agent"
            >
              <option value="all">All agents</option>
              {agentIds.map((id) => (
                <option key={id} value={id}>
                  {agentNames.get(id) || id.slice(0, 16)}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
      <div className={styles.eventList}>
        {filtered.length === 0 && (
          <div className={styles.empty}>No events yet</div>
        )}
        {filtered.map((event) => {
          const desc = extractDescription(event);
          const agentLabel =
            agentNames.get(event.agent_id || "") ||
            (event.agent_id ? event.agent_id.slice(0, 12) : "system");
          const isBroadcast = event.type === "agent.broadcast";

          return (
            <EventRow
              key={event.event_id}
              event={event}
              agentLabel={agentLabel}
              desc={desc}
              isBroadcast={isBroadcast}
              tagColor={EVENT_COLORS[event.type] || "default"}
              formatTime={formatTime}
            />
          );
        })}
      </div>
    </div>
  );
}
