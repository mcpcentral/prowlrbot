import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  Zap,
  Swords,
  Store,
  BarChart3,
  LayoutGrid,
  List,
} from "lucide-react";
import api, {
  getAnalyticsSummary,
  getCostOverTime,
  getModelBreakdown,
  getHealthStatus,
  getLevelInfo,
  getAchievements,
  listNotifications,
  getNotificationStats,
} from "../../api";
import type { UsageSummary, CostDataPoint, ModelStats } from "../../api/modules/analytics";
import styles from "./index.module.less";

// ── Types ──

interface HealthData {
  status: string;
  version: string;
  uptime_formatted: string;
  uptime_seconds: number;
  channels: Record<string, string>;
  cron_active_jobs: number;
  mcp_servers: number;
}

interface LevelData {
  level: number;
  total_xp: number;
  xp_for_next: number;
  title: string;
}

interface Achievement {
  id: string;
  name: string;
  icon: string;
  unlocked_at: string;
}

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  icon: string;
  timestamp: string;
  read: boolean;
}

interface ActivityEvent {
  id: number;
  type: string;
  text: string;
  time: string;
  tag: string;
  color: string;
  tagBg: string;
}

interface AgentInfo {
  id: string;
  name: string;
  status: string;
  model: string;
  description: string;
  icon: string;
  color: string;
}

interface MonitorInfo {
  id: string;
  name: string;
  status: "ok" | "warning" | "down" | "unknown";
  latency_ms: number | null;
}

// ── Helpers ──

function timeAgo(iso: string): string {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return "now";
  if (secs < 3600) return `${Math.floor(secs / 60)}m`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h`;
  return `${Math.floor(secs / 86400)}d`;
}

function formatCost(val: number): string {
  return `$${val.toFixed(2)}`;
}

function formatTokens(val: number): string {
  if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
  return String(val);
}

const EVENT_STYLE: Record<string, { tag: string; color: string; tagBg: string }> = {
  tool_call: { tag: "tool", color: "var(--pb-accent-purple)", tagBg: "var(--pb-tint-purple)" },
  reasoning: { tag: "think", color: "var(--pb-accent-purple)", tagBg: "var(--pb-tint-purple)" },
  task_update: { tag: "task", color: "var(--pb-accent-green)", tagBg: "var(--pb-tint-green)" },
  monitor_alert: { tag: "alert", color: "var(--pb-accent-orange)", tagBg: "var(--pb-tint-orange)" },
  mcp_request: { tag: "mcp", color: "var(--pb-accent-blue)", tagBg: "var(--pb-tint-blue)" },
  agent_status: { tag: "agent", color: "var(--pb-accent-green)", tagBg: "var(--pb-tint-green)" },
  error: { tag: "error", color: "var(--pb-accent-red)", tagBg: "var(--pb-tint-red)" },
  stream_token: { tag: "stream", color: "var(--pb-text-tertiary)", tagBg: "var(--pb-bg-hover)" },
};

function formatEventText(data: any): string {
  switch (data.type) {
    case "tool_call":
      return `Tool: ${data.data?.tool || "unknown"}${data.data?.command ? ` — ${data.data.command}` : ""}`;
    case "reasoning":
      return `Reasoning: ${(data.data?.text || "").slice(0, 80)}`;
    case "task_update":
      return `Task ${data.data?.status || "updated"}: ${data.data?.name || ""}`;
    case "monitor_alert":
      return `Alert: ${data.data?.alert || data.data?.message || ""}`;
    case "agent_status":
      return `Agent ${data.data?.status || "status change"}`;
    case "error":
      return `Error: ${data.data?.message || data.data?.error || "unknown"}`;
    default:
      return `${data.type}: ${JSON.stringify(data.data || {}).slice(0, 60)}`;
  }
}

// ── Dashboard Component ──

export default function Dashboard() {
  const navigate = useNavigate();

  // State
  const [density, setDensity] = useState<"visual" | "compact">(() => {
    return (localStorage.getItem("pb-dash-density") as "visual" | "compact") || "visual";
  });
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [costData, setCostData] = useState<CostDataPoint[]>([]);
  const [costDays, setCostDays] = useState(7);
  const [models, setModels] = useState<Record<string, ModelStats>>({});
  const [health, setHealth] = useState<HealthData | null>(null);
  const [levelData, setLevelData] = useState<LevelData | null>(null);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [monitors, setMonitors] = useState<MonitorInfo[]>([]);
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const toggleDensity = useCallback(() => {
    setDensity((d) => {
      const next = d === "visual" ? "compact" : "visual";
      localStorage.setItem("pb-dash-density", next);
      return next;
    });
  }, []);

  // ── Fetch all data on mount ──
  useEffect(() => {
    getAnalyticsSummary("day").then(setSummary).catch(() => {});
    getCostOverTime(costDays).then(setCostData).catch(() => {});
    getModelBreakdown().then(setModels).catch(() => {});

    getHealthStatus()
      .then((h: any) => setHealth(h))
      .catch(() => {});

    getLevelInfo("default")
      .then((l: any) => setLevelData(l))
      .catch(() => {});
    getAchievements("default")
      .then((a: any) => {
        if (Array.isArray(a)) setAchievements(a.slice(0, 6));
      })
      .catch(() => {});

    listNotifications(false, 10)
      .then((n: any) => {
        if (Array.isArray(n)) setNotifications(n);
      })
      .catch(() => {});
    getNotificationStats()
      .then((s: any) => {
        if (s?.unread_count != null) setUnreadCount(s.unread_count);
      })
      .catch(() => {});

    api.listSkills().then(() => {}).catch(() => {});

    api
      .listChannels()
      .then((channels: any) => {
        const list = Array.isArray(channels) ? channels : channels?.channels;
        if (Array.isArray(list)) {
          const mons: MonitorInfo[] = list.map((ch: any) => ({
            id: ch.channel || ch.id || ch.name,
            name: ch.channel || ch.name || "channel",
            status: ch.status === "connected" ? "ok" as const : ch.status === "stopped" ? "unknown" as const : "warning" as const,
            latency_ms: null,
          }));
          setMonitors(mons);
        }
      })
      .catch(() => {});

    const fetchAgents = async () => {
      try {
        const config = await api.getAgentRunningConfig();
        const agentList: AgentInfo[] = [
          {
            id: "prowlrbot",
            name: "ProwlrBot",
            status: "online",
            model: (config as any)?.model || "Auto-detect",
            description: "Main agent",
            icon: "\u26A1",
            color: "var(--pb-status-success)",
          },
        ];
        setAgents(agentList);
      } catch {
        setAgents([
          {
            id: "prowlrbot",
            name: "ProwlrBot",
            status: "online",
            model: "Auto-detect",
            description: "Main agent",
            icon: "\u26A1",
            color: "var(--pb-status-success)",
          },
        ]);
      }
    };
    fetchAgents();
  }, []);

  useEffect(() => {
    getCostOverTime(costDays).then(setCostData).catch(() => {});
  }, [costDays]);

  // ── WebSocket for live feed ──
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard?session_id=dashboard`;

    let ws: WebSocket;
    let retryTimer: ReturnType<typeof setTimeout>;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => {
          setWsConnected(false);
          retryTimer = setTimeout(connect, 5000);
        };
        ws.onerror = () => ws.close();

        ws.onmessage = (msg) => {
          try {
            const data = JSON.parse(msg.data);
            if (data.type === "ping") return;

            const style = EVENT_STYLE[data.type] || {
              tag: data.type,
              color: "var(--pb-text-tertiary)",
              tagBg: "var(--pb-bg-hover)",
            };

            const event: ActivityEvent = {
              id: Date.now() + Math.random(),
              type: data.type,
              text: formatEventText(data),
              time: new Date().toISOString(),
              tag: style.tag,
              color: style.color,
              tagBg: style.tagBg,
            };

            setActivities((prev) => [event, ...prev].slice(0, 50));
          } catch {
            // ignore
          }
        };
      } catch {
        retryTimer = setTimeout(connect, 5000);
      }
    }

    connect();
    return () => {
      clearTimeout(retryTimer);
      if (ws) ws.close();
    };
  }, []);

  // ── Derived values ──
  const systemStatus = health?.status === "healthy" ? "green" : "red";
  const modelEntries = Object.entries(models).sort(([, a], [, b]) => b.total_cost - a.total_cost);
  const xpProgress = levelData
    ? Math.min(100, Math.round((levelData.total_xp / levelData.xp_for_next) * 100))
    : 0;
  const isCompact = density === "compact";

  // ── Chart tooltip ──
  const ChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div
        style={{
          background: "var(--pb-bg-card)",
          border: "1px solid var(--pb-border)",
          borderRadius: 8,
          padding: "8px 12px",
          fontSize: 12,
        }}
      >
        <div style={{ color: "var(--pb-text-tertiary)", marginBottom: 4 }}>{label}</div>
        {payload.map((p: any) => (
          <div key={p.dataKey} style={{ color: p.color }}>
            {p.dataKey === "cost" ? formatCost(p.value) : formatTokens(p.value)}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={styles.dashboard}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div>
            <div className={styles.headerTitle}>Dashboard</div>
            <div className={styles.headerMeta}>
              Overview
              {health ? ` \u00b7 Uptime: ${health.uptime_formatted || ""}` : ""}
              {summary ? ` \u00b7 ${summary.total_queries} queries today` : ""}
            </div>
          </div>
        </div>
        <div className={styles.headerRight}>
          <div
            className={`${styles.statusBadge} ${systemStatus === "green" ? styles.statusGreen : styles.statusRed}`}
          >
            <span>{"\u25CF"}</span>
            {systemStatus === "green" ? "All Systems Go" : "Issues Detected"}
          </div>
          <button className={styles.densityToggle} onClick={toggleDensity} title="Toggle density">
            {isCompact ? <List size={14} /> : <LayoutGrid size={14} />}
            {isCompact ? "Compact" : "Visual"}
          </button>
        </div>
      </div>

      {/* ── Dashboard Grid ── */}
      <div className={styles.grid}>
        {/* ── Row 1: Stat Panels ── */}
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-accent-blue)" }}>
              {summary?.total_queries ?? "\u2014"}
            </div>
            <div className={styles.statLabel}>Queries Today</div>
            {!isCompact && (
              <div className={`${styles.statDelta} ${styles.deltaUp}`}>{"\u25B2"} active</div>
            )}
          </div>
        </div>

        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-status-success)" }}>
              {summary ? formatCost(summary.total_cost) : "\u2014"}
            </div>
            <div className={styles.statLabel}>Cost Today</div>
            {!isCompact && (
              <div className={`${styles.statDelta} ${styles.deltaNeutral}`}>
                {summary?.avg_latency_ms ? `${Math.round(summary.avg_latency_ms)}ms avg` : "\u2014"}
              </div>
            )}
          </div>
        </div>

        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-accent-orange)" }}>
              {agents.length || "\u2014"}
            </div>
            <div className={styles.statLabel}>Active Agents</div>
            {!isCompact && (
              <div className={`${styles.statDelta} ${styles.deltaNeutral}`}>
                {health?.mcp_servers ? `${health.mcp_servers} MCP` : ""}
              </div>
            )}
          </div>
        </div>

        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.statPanel}>
            <div className={styles.statValue} style={{ color: "var(--pb-text-secondary)" }}>
              {summary ? formatTokens(summary.total_tokens) : "\u2014"}
            </div>
            <div className={styles.statLabel}>Tokens Used</div>
            {!isCompact && costData.length > 0 && (
              <div className={styles.statSpark}>
                {costData.slice(-7).map((d, i) => {
                  const max = Math.max(...costData.slice(-7).map((x) => x.tokens || 1));
                  const h = Math.max(10, ((d.tokens || 0) / max) * 100);
                  return (
                    <div
                      key={i}
                      className={styles.sparkBar}
                      style={{
                        height: `${h}%`,
                        background:
                          i === costData.slice(-7).length - 1
                            ? "var(--pb-accent-purple)"
                            : undefined,
                      }}
                    />
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── Row 2: Cost Chart (3 cols) + Agents (1 col) ── */}
        {!isCompact && (
          <div className={`${styles.panel} ${styles.col3}`}>
            <div className={styles.panelHeader}>
              <div className={styles.panelTitle}>Cost & Usage</div>
              <div className={styles.panelActions}>
                {[7, 30, 90].map((d) => (
                  <span
                    key={d}
                    className={`${styles.panelAction} ${costDays === d ? styles.panelActionActive : ""}`}
                    onClick={() => setCostDays(d)}
                  >
                    {d}d
                  </span>
                ))}
              </div>
            </div>
            <div className={styles.panelBody} style={{ height: 200 }}>
              {costData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={costData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="var(--pb-border)" strokeDasharray="4 4" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: "var(--pb-text-tertiary)", fontSize: 11 }}
                      axisLine={{ stroke: "var(--pb-border)" }}
                      tickLine={false}
                      tickFormatter={(v) => {
                        const d = new Date(v);
                        return `${d.getMonth() + 1}/${d.getDate()}`;
                      }}
                    />
                    <YAxis
                      tick={{ fill: "var(--pb-text-tertiary)", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v) => `$${v}`}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <defs>
                      <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--pb-accent-purple)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="var(--pb-accent-purple)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="cost"
                      stroke="var(--pb-accent-purple)"
                      strokeWidth={2}
                      fill="url(#costGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className={styles.emptyState}>No cost data yet — usage will appear here</div>
              )}
            </div>
          </div>
        )}

        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Agents</div>
            <span
              className={styles.panelAction}
              onClick={() => navigate("/agent-config")}
            >
              Manage {"\u2192"}
            </span>
          </div>
          <div className={styles.panelBody}>
            {agents.map((agent) => (
              <div key={agent.id} className={styles.agentRow}>
                <div className={styles.agentAvatar} style={{ color: agent.color }}>
                  {agent.icon}
                </div>
                <div className={styles.agentInfo}>
                  <div className={styles.agentName}>{agent.name}</div>
                  <div className={styles.agentDesc}>
                    {agent.description} &bull; {agent.model}
                  </div>
                </div>
                <div
                  className={styles.agentStatus}
                  style={{
                    background:
                      agent.status === "online"
                        ? "var(--pb-status-success)"
                        : "var(--pb-status-neutral)",
                  }}
                  title={agent.status}
                />
              </div>
            ))}

            {levelData && (
              <div className={styles.xpSection}>
                <div className={styles.xpHeader}>
                  <span className={styles.xpLevel}>Lv. {levelData.level}</span>
                  <span className={styles.xpTitle}>{levelData.title || "Operator"}</span>
                </div>
                <div className={styles.xpBarBg}>
                  <div className={styles.xpBarFill} style={{ width: `${xpProgress}%` }} />
                </div>
                <div className={styles.xpBarLabel}>
                  <span>{levelData.total_xp} XP</span>
                  <span>{levelData.xp_for_next} XP</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Row 3: Live Feed + Monitors + Quick Actions / Notifs ── */}
        <div
          className={`${styles.panel} ${styles.col2}`}
          style={{ maxHeight: isCompact ? 200 : 340 }}
        >
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              Live Feed
              {wsConnected && <span className={styles.liveDot} />}
            </div>
            <span style={{ fontSize: 11, color: wsConnected ? "var(--pb-status-success)" : "var(--pb-text-tertiary)" }}>
              {wsConnected ? "LIVE" : "CONNECTING..."}
            </span>
          </div>
          <div className={`${styles.panelBody} ${styles.panelScroll}`}>
            {activities.length === 0 ? (
              <div className={styles.emptyState}>
                Watching for events... Activity will appear in real-time
              </div>
            ) : (
              activities.map((event) => (
                <div key={event.id} className={styles.feedItem}>
                  <div className={styles.feedDot} style={{ background: event.color }} />
                  <div style={{ flex: 1 }}>
                    <div className={styles.feedText}>{event.text}</div>
                    <span
                      className={styles.feedTag}
                      style={{ background: event.tagBg, color: event.color }}
                    >
                      {event.tag}
                    </span>
                  </div>
                  <div className={styles.feedTime}>{timeAgo(event.time)}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Monitors + Model Breakdown */}
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Monitors</div>
          </div>
          <div className={styles.panelBody}>
            {monitors.length > 0 ? (
              <div className={styles.monitorGrid}>
                {monitors.map((m) => (
                  <div key={m.id} className={styles.monitorItem}>
                    <div
                      className={styles.monitorDot}
                      style={{
                        background:
                          m.status === "ok"
                            ? "var(--pb-status-success)"
                            : m.status === "warning"
                              ? "var(--pb-status-warning)"
                              : m.status === "down"
                                ? "var(--pb-status-error)"
                                : "var(--pb-status-neutral)",
                      }}
                    />
                    <div className={styles.monitorLatency}>
                      {m.latency_ms != null ? `${m.latency_ms}ms` : "\u2014"}
                    </div>
                    <div className={styles.monitorName}>{m.name}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.emptyState}>No monitors configured</div>
            )}

            {modelEntries.length > 0 && (
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--pb-border)" }}>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--pb-text-tertiary)",
                    textTransform: "uppercase" as const,
                    letterSpacing: 0.5,
                    marginBottom: 8,
                  }}
                >
                  Model Breakdown
                </div>
                {modelEntries.slice(0, 5).map(([name, stats]) => (
                  <div key={name} className={styles.modelRow}>
                    <span className={styles.modelName}>{name}</span>
                    <span className={styles.modelCost}>{formatCost(stats.total_cost)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions + Notifications + Achievements */}
        <div className={`${styles.panel} ${styles.col1}`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Quick Launch</div>
          </div>
          <div className={styles.panelBody}>
            <button
              className={`${styles.actionBtn} ${styles.actionPrimary}`}
              onClick={() => navigate("/chat")}
            >
              <Zap size={14} /> New Chat
            </button>
            <button
              className={`${styles.actionBtn} ${styles.actionSecondary}`}
              onClick={() => navigate("/warroom")}
            >
              <Swords size={14} /> War Room
            </button>
            <button
              className={`${styles.actionBtn} ${styles.actionSecondary}`}
              onClick={() => navigate("/marketplace")}
            >
              <Store size={14} /> Marketplace
            </button>
            <button
              className={`${styles.actionBtn} ${styles.actionSecondary}`}
              onClick={() => navigate("/analytics")}
            >
              <BarChart3 size={14} /> Analytics
            </button>
          </div>

          {/* Notifications */}
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Notifications</div>
            {unreadCount > 0 && (
              <span className={styles.alertBadge}>{unreadCount}</span>
            )}
          </div>
          <div className={`${styles.panelBody} ${styles.panelScroll}`} style={{ maxHeight: 140 }}>
            {notifications.length > 0 ? (
              notifications.map((n) => (
                <div key={n.id} className={styles.notifRow}>
                  <span className={styles.notifIcon}>{n.icon || "\uD83D\uDD14"}</span>
                  <span className={styles.notifText}>{n.title || n.message}</span>
                  <span className={styles.notifTime}>{timeAgo(n.timestamp)}</span>
                </div>
              ))
            ) : (
              <div className={styles.emptyState}>No notifications</div>
            )}
          </div>

          {/* Achievements */}
          {achievements.length > 0 && (
            <div style={{ padding: "12px 16px", borderTop: "1px solid var(--pb-border)" }}>
              <div
                style={{
                  fontSize: 11,
                  color: "var(--pb-text-tertiary)",
                  textTransform: "uppercase" as const,
                  letterSpacing: 0.5,
                  marginBottom: 8,
                }}
              >
                Achievements
              </div>
              <div>
                {achievements.map((a) => (
                  <span key={a.id} className={styles.achievementPill}>
                    {a.icon} {a.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
