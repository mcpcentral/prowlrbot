import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "antd";
import {
  Bot,
  Zap,
  Activity,
  Shield,
  Wifi,
  Plus,
  Sparkles,
  Eye,
  MessageSquare,
  Globe,
  Layers,
} from "lucide-react";
import api from "../../api";
import styles from "./index.module.less";

// ── Types ──
interface AgentInfo {
  id: string;
  name: string;
  avatar: string;
  color: string;
  status: "online" | "idle" | "offline";
  model: string;
  skills: string[];
  autonomy: string;
}

interface ActivityEvent {
  id: number;
  type: string;
  text: string;
  time: string;
  icon: string;
  color: string;
}

// ── Avatar emoji map ──
const AVATAR_EMOJI: Record<string, string> = {
  robot: "\u{1F916}",
  cat: "\u{1F431}",
  dog: "\u{1F436}",
  fox: "\u{1F98A}",
  owl: "\u{1F989}",
  dragon: "\u{1F409}",
  paw: "\u{1F43E}",
};

// ── Helpers ──
function timeAgo(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const secs = Math.floor((now - d.getTime()) / 1000);
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

const EVENT_ICON_MAP: Record<string, { icon: string; bg: string }> = {
  tool_call: { icon: "\u{1F527}", bg: "var(--pb-tint-blue)" },
  reasoning: { icon: "\u{1F9E0}", bg: "var(--pb-tint-orange)" },
  task_update: { icon: "\u{2705}", bg: "var(--pb-tint-green)" },
  monitor_alert: { icon: "\u{1F6A8}", bg: "var(--pb-tint-red)" },
  mcp_request: { icon: "\u{1F50C}", bg: "var(--pb-tint-blue)" },
  stream_token: { icon: "\u{1F4AC}", bg: "var(--pb-tint-purple)" },
  agent_status: { icon: "\u{1F916}", bg: "var(--pb-bg-sunken)" },
  error: { icon: "\u{274C}", bg: "var(--pb-tint-red)" },
};

// ── Default demo agents when no agents are configured ──
const DEFAULT_AGENTS: AgentInfo[] = [
  {
    id: "prowlr-main",
    name: "ProwlrBot",
    avatar: "paw",
    color: "#6B5CE7",
    status: "online",
    model: "Auto-detect",
    skills: ["shell", "file_io", "browser"],
    autonomy: "guide",
  },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [agents] = useState<AgentInfo[]>(DEFAULT_AGENTS);
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [stats, setStats] = useState({
    agents: 1,
    channels: 0,
    skills: 0,
    uptime: "—",
  });
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Load initial data
  useEffect(() => {
    // Load channels count
    api
      .listChannels()
      .then((channels: any) => {
        const list = Array.isArray(channels) ? channels : channels?.channels;
        if (Array.isArray(list)) {
          setStats((s) => ({ ...s, channels: list.length }));
        }
      })
      .catch(() => {});

    // Load skills count
    api
      .listSkills()
      .then((skills: any) => {
        if (Array.isArray(skills)) {
          setStats((s) => ({ ...s, skills: skills.length }));
        }
      })
      .catch(() => {});

    // Load version for uptime display
    api
      .getVersion()
      .then((v: any) => {
        if (v?.version) {
          setStats((s) => ({ ...s, uptime: `v${v.version}` }));
        }
      })
      .catch(() => {});
  }, []);

  // WebSocket connection for real-time events
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

            const meta = EVENT_ICON_MAP[data.type] || {
              icon: "\u{1F4E1}",
              bg: "var(--pb-bg-sunken)",
            };
            const event: ActivityEvent = {
              id: Date.now() + Math.random(),
              type: data.type,
              text: formatEventText(data),
              time: new Date().toISOString(),
              icon: meta.icon,
              color: meta.bg,
            };

            setActivities((prev) => [event, ...prev].slice(0, 50));
          } catch {
            // ignore parse errors
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

  function formatEventText(data: any): string {
    switch (data.type) {
      case "tool_call":
        return `Tool: ${data.data?.tool || "unknown"} ${data.data?.command ? `— ${data.data.command}` : ""}`;
      case "reasoning":
        return `Agent reasoning: ${(data.data?.text || "").slice(0, 80)}...`;
      case "task_update":
        return `Task ${data.data?.status || "updated"}: ${data.data?.name || ""}`;
      case "monitor_alert":
        return `Alert: ${data.data?.alert || data.data?.message || ""}`;
      case "agent_status":
        return `Agent ${data.data?.status || "status change"}`;
      default:
        return `${data.type}: ${JSON.stringify(data.data || {}).slice(0, 60)}`;
    }
  }

  // ── Stat Cards ──
  const statCards = [
    {
      icon: <Bot size={22} />,
      bg: "var(--pb-tint-blue)",
      iconColor: "var(--pb-icon-blue)",
      value: stats.agents,
      label: "Active Agents",
    },
    {
      icon: <Wifi size={22} />,
      bg: "var(--pb-tint-green)",
      iconColor: "var(--pb-icon-green)",
      value: stats.channels,
      label: "Channels",
    },
    {
      icon: <Sparkles size={22} />,
      bg: "var(--pb-tint-orange)",
      iconColor: "var(--pb-icon-orange)",
      value: stats.skills,
      label: "Skills",
    },
    {
      icon: <Shield size={22} />,
      bg: "var(--pb-tint-purple)",
      iconColor: "var(--pb-icon-purple)",
      value: stats.uptime,
      label: "Version",
    },
  ];

  // ── Quick Actions ──
  const quickActions = [
    {
      icon: <Plus size={16} />,
      bg: "var(--pb-tint-blue)",
      label: "New Agent",
      onClick: () => navigate("/agent-config"),
    },
    {
      icon: <MessageSquare size={16} />,
      bg: "var(--pb-tint-green)",
      label: "Open Chat",
      onClick: () => navigate("/chat"),
    },
    {
      icon: <Layers size={16} />,
      bg: "var(--pb-tint-orange)",
      label: "Manage Skills",
      onClick: () => navigate("/skills"),
    },
    {
      icon: <Globe size={16} />,
      bg: "var(--pb-tint-purple)",
      label: "Channels",
      onClick: () => navigate("/channels"),
    },
  ];

  return (
    <div className={styles.dashboard}>
      {/* ── Stats Row ── */}
      <div className={styles.statsRow}>
        {statCards.map((card, i) => (
          <div key={i} className={styles.statCard}>
            <div
              className={styles.statIcon}
              style={{ background: card.bg, color: card.iconColor }}
            >
              {card.icon}
            </div>
            <div className={styles.statInfo}>
              <div className={styles.statValue}>{card.value}</div>
              <div className={styles.statLabel}>{card.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Main Grid ── */}
      <div className={styles.mainGrid}>
        {/* ── Left: Agents Panel ── */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>
              <Bot size={16} /> Your Agents
            </span>
            <Button
              type="text"
              size="small"
              icon={<Plus size={14} />}
              onClick={() => navigate("/agent-config")}
            >
              Add
            </Button>
          </div>

          {agents.length === 0 ? (
            <div className={styles.emptyState}>
              <Bot size={40} strokeWidth={1} />
              <div className={styles.emptyText}>
                No agents configured yet. Create one to get started!
              </div>
              <Button type="primary" onClick={() => navigate("/agent-config")}>
                Create Agent
              </Button>
            </div>
          ) : (
            <div className={styles.agentGrid}>
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={styles.agentCard}
                  onClick={() => navigate("/chat")}
                >
                  <div
                    className={styles.agentAvatar}
                    style={{ background: agent.color }}
                  >
                    {AVATAR_EMOJI[agent.avatar] || AVATAR_EMOJI.robot}
                  </div>
                  <div className={styles.agentInfo}>
                    <div className={styles.agentName}>{agent.name}</div>
                    <div className={styles.agentMeta}>
                      <span
                        className={`${styles.agentStatus} ${
                          agent.status === "online"
                            ? styles.agentStatusOnline
                            : agent.status === "idle"
                              ? styles.agentStatusIdle
                              : styles.agentStatusOffline
                        }`}
                      />
                      {agent.status} &middot; {agent.model}
                    </div>
                    <div className={styles.agentTags}>
                      {agent.skills.slice(0, 3).map((s) => (
                        <span key={s} className={styles.agentTag}>
                          {s}
                        </span>
                      ))}
                      {agent.skills.length > 3 && (
                        <span className={styles.agentTag}>
                          +{agent.skills.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Add Agent card */}
              <div
                className={styles.agentCard}
                onClick={() => navigate("/agent-config")}
                style={{
                  justifyContent: "center",
                  alignItems: "center",
                  borderStyle: "dashed",
                  minHeight: 100,
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                <Plus size={24} color="var(--pb-text-disabled)" />
                <span style={{ fontSize: 13, color: "var(--pb-text-tertiary)" }}>
                  Add Agent
                </span>
              </div>
            </div>
          )}
        </div>

        {/* ── Right Sidebar ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Quick Actions */}
          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <span className={styles.panelTitle}>
                <Zap size={16} /> Quick Actions
              </span>
            </div>
            <div className={styles.quickActions}>
              {quickActions.map((action, i) => (
                <div
                  key={i}
                  className={styles.quickAction}
                  onClick={action.onClick}
                >
                  <div
                    className={styles.quickActionIcon}
                    style={{ background: action.bg }}
                  >
                    {action.icon}
                  </div>
                  <span className={styles.quickActionLabel}>
                    {action.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Activity Feed */}
          <div className={styles.panel} style={{ flex: 1, minHeight: 0 }}>
            <div className={styles.panelHeader}>
              <span className={styles.panelTitle}>
                <Activity size={16} /> Activity Feed
                {wsConnected && (
                  <span
                    className={`${styles.healthDot} ${styles.healthGreen}`}
                    style={{ marginLeft: 4 }}
                  />
                )}
              </span>
              <span style={{ fontSize: 11, color: "var(--pb-text-disabled)" }}>
                {wsConnected ? "Live" : "Connecting..."}
              </span>
            </div>
            <div className={styles.panelBody}>
              {activities.length === 0 ? (
                <div className={styles.emptyState} style={{ padding: "20px 0" }}>
                  <Eye size={28} strokeWidth={1} />
                  <div className={styles.emptyText} style={{ fontSize: 12 }}>
                    Watching for events...
                    <br />
                    Activity will appear here in real-time
                  </div>
                </div>
              ) : (
                activities.map((event) => (
                  <div key={event.id} className={styles.activityItem}>
                    <div
                      className={styles.activityIcon}
                      style={{ background: event.color }}
                    >
                      {event.icon}
                    </div>
                    <div className={styles.activityContent}>
                      <div className={styles.activityText}>{event.text}</div>
                      <div className={styles.activityTime}>
                        {timeAgo(event.time)}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
