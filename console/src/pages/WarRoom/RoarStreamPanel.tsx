import { useEffect, useState, useCallback } from "react";
import type { RoarStreamEvent } from "../../api/roar";
import { subscribeRoarStream } from "../../api/roar";
import styles from "./RoarStreamPanel.module.less";

const ROAR_TYPE_LABELS: Record<string, string> = {
  reasoning: "Reasoning",
  tool_call: "Tool call",
  task_update: "Task update",
  agent_status: "Status",
  mcp_request: "MCP",
  monitor_alert: "Alert",
  checkpoint: "Checkpoint",
  world_update: "World",
};

export default function RoarStreamPanel() {
  const [events, setEvents] = useState<RoarStreamEvent[]>([]);
  const [connected, setConnected] = useState(false);

  const onEvent = useCallback((ev: RoarStreamEvent) => {
    setEvents((prev) => [ev, ...prev].slice(0, 100));
  }, []);

  useEffect(() => {
    const disconnect = subscribeRoarStream(onEvent, setConnected);
    return disconnect;
  }, [onEvent]);

  const formatTime = (ts: number) => {
    try {
      return new Date(ts * 1000).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return "--:--";
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.title}>
          ROAR stream
          <span className={styles.badge}>ROAR</span>
        </span>
        <span
          className={connected ? styles.connected : styles.disconnected}
          title={connected ? "Connected to /roar/events" : "Not connected"}
        >
          {connected ? "Live" : "Off"}
        </span>
      </div>
      <div className={styles.list}>
        {events.length === 0 && (
          <div className={styles.empty}>
            {connected
              ? "Waiting for ROAR events (reasoning, tool_call, task_update…)"
              : "ROAR SSE not available. Start the app with ROAR server."}
          </div>
        )}
        {events.map((ev, i) => (
          <div key={`${ev.timestamp}-${i}`} className={styles.row}>
            <span className={styles.time}>{formatTime(ev.timestamp)}</span>
            <span className={styles.type}>
              {ROAR_TYPE_LABELS[ev.type] ?? ev.type}
            </span>
            {ev.source && (
              <span className={styles.source} title={ev.source}>
                {ev.source.replace(/^did:roar:agent:/, "").slice(0, 16)}
              </span>
            )}
            <span className={styles.data}>
              {ev.type === "reasoning" && ev.data?.thought != null
                ? String(ev.data.thought)
                : ev.type === "task_update" && ev.data?.note != null
                  ? String(ev.data.note)
                  : JSON.stringify(ev.data).slice(0, 80)}
              {JSON.stringify(ev.data).length > 80 ? "…" : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
