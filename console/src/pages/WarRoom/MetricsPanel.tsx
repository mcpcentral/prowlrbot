import { useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import type { Agent, Task, WarRoomEvent, FileLock } from "../../api/warroom";

interface MetricsPanelProps {
  agents: Agent[];
  tasks: Task[];
  events: WarRoomEvent[];
  conflicts: FileLock[];
}

const PIE_COLORS: Record<string, string> = {
  idle: "var(--pb-chart-pie-idle)",
  working: "var(--pb-chart-pie-working)",
  disconnected: "var(--pb-chart-pie-disconnected)",
};

const STATUS_LABELS: Record<string, string> = {
  idle: "Idle",
  working: "Working",
  disconnected: "Disconnected",
};

/** Build hourly buckets from events of a given type, looking back `hoursBack` hours. */
function buildHourlyBuckets(
  events: WarRoomEvent[],
  eventType: string,
  hoursBack: number,
): { hour: string; count: number }[] {
  const now = Date.now();
  const cutoff = now - hoursBack * 3600000;
  const filtered = events.filter(
    (e) => e.type === eventType && new Date(e.timestamp).getTime() >= cutoff,
  );

  const hourMap = new Map<string, number>();

  // Pre-fill all hour slots so chart shows continuous data
  for (let i = hoursBack - 1; i >= 0; i--) {
    const h = new Date(now - i * 3600000);
    const key = `${h.getHours()}:00`;
    hourMap.set(key, 0);
  }

  for (const e of filtered) {
    const d = new Date(e.timestamp);
    const key = `${d.getHours()}:00`;
    hourMap.set(key, (hourMap.get(key) || 0) + 1);
  }

  return [...hourMap.entries()].map(([hour, count]) => ({ hour, count }));
}

/** A single stat card. */
function StatCard({
  label,
  value,
  suffix,
  color,
}: {
  label: string;
  value: number | string;
  suffix?: string;
  color: string;
}) {
  return (
    <div
      style={{
        background: "var(--pb-wr-bg-card)",
        border: "1px solid var(--pb-wr-border-strong)",
        borderRadius: 8,
        padding: "12px 16px",
        flex: 1,
        minWidth: 120,
      }}
    >
      <div
        style={{
          color: "var(--pb-wr-text-dim)",
          fontSize: 10,
          textTransform: "uppercase",
          letterSpacing: 1,
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div style={{ color, fontSize: 24, fontWeight: 700, lineHeight: 1.2 }}>
        {value}
        {suffix && (
          <span style={{ fontSize: 12, fontWeight: 400, color: "var(--pb-wr-text-secondary)", marginLeft: 4 }}>
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

export default function MetricsPanel({ agents, tasks, events, conflicts }: MetricsPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  // Summary statistics
  const stats = useMemo(() => {
    const totalAgents = agents.length;
    const activeAgents = agents.filter((a) => a.status !== "disconnected").length;
    const workingAgents = agents.filter((a) => a.status === "working").length;
    const activeTasks = tasks.filter((t) => t.status !== "done" && t.status !== "failed").length;
    const completedTasks = tasks.filter((t) => t.status === "done").length;
    const failedTasks = tasks.filter((t) => t.status === "failed").length;
    const totalFinished = completedTasks + failedTasks;
    const completionRate = totalFinished > 0 ? Math.round((completedTasks / totalFinished) * 100) : 0;
    const activeLocks = conflicts.length;

    return {
      totalAgents,
      activeAgents,
      workingAgents,
      activeTasks,
      completedTasks,
      completionRate,
      totalFinished,
      activeLocks,
    };
  }, [agents, tasks, conflicts]);

  // Agent utilization pie data
  const utilization = useMemo(() => {
    const counts = { idle: 0, working: 0, disconnected: 0 };
    for (const a of agents) {
      const s = a.status as keyof typeof counts;
      if (s in counts) counts[s]++;
      else counts.idle++;
    }
    return Object.entries(counts)
      .filter(([, v]) => v > 0)
      .map(([name, value]) => ({ name, value }));
  }, [agents]);

  // Task velocity -- completions per hour (last 12 hours)
  const velocity = useMemo(() => buildHourlyBuckets(events, "task.completed", 12), [events]);

  // Lock contention -- lock.acquired events per hour (last 12 hours)
  const lockContention = useMemo(() => buildHourlyBuckets(events, "lock.acquired", 12), [events]);

  const chartTooltipStyle = {
    background: "var(--pb-wr-bg-card)",
    border: "1px solid var(--pb-wr-border-strong)",
    borderRadius: 4,
    fontSize: 11,
  };

  if (collapsed) {
    return (
      <div
        onClick={() => setCollapsed(false)}
        style={{
          background: "var(--pb-wr-bg-panel)",
          border: "1px solid var(--pb-wr-border)",
          borderRadius: 8,
          padding: "10px 16px",
          cursor: "pointer",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            color: "var(--pb-wr-accent)",
            fontSize: 13,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: 1,
          }}
        >
          Metrics
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ color: "var(--pb-wr-text-secondary)", fontSize: 11 }}>
            {stats.activeAgents} agents | {stats.activeTasks} tasks | {stats.activeLocks} locks
          </span>
          <span style={{ color: "var(--pb-wr-text-tertiary)", fontSize: 11 }}>Click to expand</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: "var(--pb-wr-bg-panel)", border: "1px solid var(--pb-wr-border)", borderRadius: 8, padding: 16 }}>
      {/* Header */}
      <div
        onClick={() => setCollapsed(true)}
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
          cursor: "pointer",
        }}
      >
        <span
          style={{
            color: "var(--pb-wr-accent)",
            fontSize: 13,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: 1,
          }}
        >
          Metrics
        </span>
        <span style={{ color: "var(--pb-wr-text-tertiary)", fontSize: 11 }}>Click to collapse</span>
      </div>

      {/* Summary Stats Row */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <StatCard
          label="Active Agents"
          value={stats.activeAgents}
          suffix={`/ ${stats.totalAgents}`}
          color="var(--pb-wr-status-done)"
        />
        <StatCard
          label="Working"
          value={stats.workingAgents}
          color="var(--pb-wr-status-progress)"
        />
        <StatCard
          label="Active Tasks"
          value={stats.activeTasks}
          color="var(--pb-status-warning)"
        />
        <StatCard
          label="Completed"
          value={stats.completedTasks}
          color="var(--pb-wr-accent)"
        />
        <StatCard
          label="Success Rate"
          value={stats.totalFinished > 0 ? `${stats.completionRate}%` : "--"}
          color={stats.completionRate >= 80 ? "var(--pb-wr-status-done)" : stats.completionRate >= 50 ? "var(--pb-status-warning)" : "var(--pb-wr-status-failed)"}
        />
        <StatCard
          label="File Locks"
          value={stats.activeLocks}
          color={stats.activeLocks > 0 ? "var(--pb-wr-lock-active)" : "var(--pb-wr-text-tertiary)"}
        />
      </div>

      {/* Charts Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        {/* Task Velocity */}
        <div>
          <div
            style={{
              color: "var(--pb-wr-text-secondary)",
              fontSize: 11,
              marginBottom: 8,
              textTransform: "uppercase",
              letterSpacing: 1,
            }}
          >
            Task Velocity (tasks/hr)
          </div>
          <ResponsiveContainer width="100%" height={140}>
            <AreaChart data={velocity}>
              <defs>
                <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--pb-wr-accent)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--pb-wr-accent)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--pb-wr-border)" />
              <XAxis
                dataKey="hour"
                tick={{ fill: "var(--pb-chart-tick)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide allowDecimals={false} />
              <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "var(--pb-wr-text-secondary)" }} />
              <Area
                type="monotone"
                dataKey="count"
                name="Tasks"
                stroke="var(--pb-wr-accent)"
                fill="url(#tealGrad)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Utilization */}
        <div>
          <div
            style={{
              color: "var(--pb-wr-text-secondary)",
              fontSize: 11,
              marginBottom: 8,
              textTransform: "uppercase",
              letterSpacing: 1,
            }}
          >
            Agent Utilization
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <ResponsiveContainer width={120} height={140}>
              <PieChart>
                <Pie
                  data={utilization}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={55}
                >
                  {utilization.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={PIE_COLORS[entry.name] || "var(--pb-chart-pie-disconnected)"}
                    />
                  ))}
                </Pie>
                <Tooltip contentStyle={chartTooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {utilization.map((entry) => (
                <div
                  key={entry.name}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    fontSize: 11,
                    color: "var(--pb-wr-text-secondary)",
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: PIE_COLORS[entry.name] || "var(--pb-chart-pie-disconnected)",
                      flexShrink: 0,
                    }}
                  />
                  {STATUS_LABELS[entry.name] || entry.name}: {entry.value}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Lock Contention */}
        <div>
          <div
            style={{
              color: "var(--pb-wr-text-secondary)",
              fontSize: 11,
              marginBottom: 8,
              textTransform: "uppercase",
              letterSpacing: 1,
            }}
          >
            Lock Contention (locks/hr)
          </div>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={lockContention}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--pb-wr-border)" />
              <XAxis
                dataKey="hour"
                tick={{ fill: "var(--pb-chart-tick)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide allowDecimals={false} />
              <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "var(--pb-wr-text-secondary)" }} />
              <Bar dataKey="count" name="Locks" fill="var(--pb-wr-lock-active)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
