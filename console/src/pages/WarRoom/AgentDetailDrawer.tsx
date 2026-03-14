import { useMemo } from "react";
import { Drawer } from "antd";
import type { Agent, Task, WarRoomEvent } from "../../api/warroom";
import styles from "./AgentDetailDrawer.module.less";

interface AgentDetailDrawerProps {
  agent: Agent | null;
  tasks: Task[];
  events: WarRoomEvent[];
  onClose: () => void;
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

function eventSummary(ev: WarRoomEvent): string {
  const p = ev.payload;
  if (ev.type === "agent.broadcast" && p?.message) return String(p.message);
  if (ev.type === "task.claimed" && p?.title) return `Claimed: ${p.title}`;
  if (ev.type === "task.updated" && p?.note) return String(p.note);
  if (ev.type === "task.completed") return "Completed task";
  if (ev.type === "task.failed" && p?.reason) return String(p.reason);
  if (ev.type === "finding.shared" && p?.key) return `Shared: ${p.key}`;
  if (p?.message) return String(p.message);
  if (p?.title) return String(p.title);
  return ev.type;
}

export default function AgentDetailDrawer({
  agent,
  tasks,
  events,
  onClose,
}: AgentDetailDrawerProps) {
  const currentTask = useMemo(() => {
    if (!agent?.current_task_id) return null;
    return tasks.find((t) => t.task_id === agent.current_task_id) ?? null;
  }, [agent?.current_task_id, tasks]);

  const agentEvents = useMemo(() => {
    if (!agent) return [];
    return events
      .filter((e) => e.agent_id === agent.agent_id)
      .slice(0, 50);
  }, [agent, events]);

  if (!agent) return null;

  return (
    <Drawer
      title={
        <span className={styles.drawerTitle}>
          <span
            className={`${styles.dot} ${
              agent.status === "working"
                ? styles.dotWorking
                : agent.status === "disconnected"
                  ? styles.dotOffline
                  : styles.dotIdle
            }`}
          />
          {agent.name}
        </span>
      }
      open={!!agent}
      onClose={onClose}
      width={420}
      styles={{
        header: {
          background: "var(--pb-bg-card)",
          borderBottom: "1px solid var(--pb-border)",
          color: "var(--pb-text-primary)",
        },
        body: {
          background: "var(--pb-bg-page)",
          color: "var(--pb-text-primary)",
        },
      }}
    >
      <div className={styles.body}>
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Status</div>
          <span className={styles.statusBadge} data-status={agent.status}>
            {agent.status}
          </span>
          {agent.capabilities.length > 0 && (
            <div className={styles.tags}>
              {agent.capabilities.map((c) => (
                <span key={c} className={styles.tag}>
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>

        {currentTask && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>Current task</div>
            <div className={styles.taskCard}>
              <div className={styles.taskTitle}>{currentTask.title}</div>
              {currentTask.description && (
                <div className={styles.taskDesc}>{currentTask.description}</div>
              )}
              {currentTask.progress_note && (
                <div className={styles.progressNote}>
                  {currentTask.progress_note}
                </div>
              )}
            </div>
          </div>
        )}

        <div className={styles.section}>
          <div className={styles.sectionLabel}>Timeline</div>
          {agentEvents.length === 0 ? (
            <div className={styles.empty}>No events yet</div>
          ) : (
            <div className={styles.timeline}>
              {agentEvents.map((ev) => (
                <div key={ev.event_id} className={styles.timelineRow}>
                  <span className={styles.timelineTime}>
                    {formatTime(ev.timestamp)}
                  </span>
                  <span className={styles.timelineType}>{ev.type}</span>
                  <span className={styles.timelineDesc}>
                    {eventSummary(ev)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Drawer>
  );
}
