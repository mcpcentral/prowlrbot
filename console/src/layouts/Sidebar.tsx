import { Layout, Menu, type MenuProps } from "antd";
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api";
import type { ConsolePluginManifest } from "../api";
import {
  LayoutDashboard,
  MessageSquare,
  Radio,
  Zap,
  MessageCircle,
  Wifi,
  UsersRound,
  CalendarClock,
  Sparkles,
  Briefcase,
  Cpu,
  Box,
  Globe,
  Settings,
  Plug,
  Store,
  Shield,
  Eye,
  Palette,
  Bot,
  BarChart3,
  HardDrive,
  Trophy,
} from "lucide-react";

const { Sider } = Layout;

const BASE_KEY_TO_PATH: Record<string, string> = {
  dashboard: "/dashboard",
  chat: "/chat",
  channels: "/channels",
  sessions: "/sessions",
  "cron-jobs": "/cron-jobs",
  skills: "/skills",
  mcp: "/mcp",
  workspace: "/workspace",
  models: "/models",
  environments: "/environments",
  "agent-config": "/agent-config",
  marketplace: "/marketplace",
  agentverse: "/agentverse",
  security: "/security",
  privacy: "/privacy",
  appearance: "/appearance",
  warroom: "/warroom",
  monitoring: "/monitoring",
  memory: "/memory",
  swarm: "/swarm",
  "team-builder": "/team-builder",
  credits: "/credits",
  replay: "/replay",
  terminal: "/terminal",
  analytics: "/analytics",
  hardware: "/hardware",
  leaderboard: "/leaderboard",
  "ui-gallery": "/ui-gallery",
};

const PLUGIN_ICON_MAP: Record<string, React.ReactNode> = {
  Radio: <Radio size={16} />,
  BarChart3: <BarChart3 size={16} />,
  Trophy: <Trophy size={16} />,
  Plug: <Plug size={16} />,
  LayoutDashboard: <LayoutDashboard size={16} />,
  Eye: <Eye size={16} />,
  Sparkles: <Sparkles size={16} />,
};

interface SidebarProps {
  selectedKey: string;
  plugins?: ConsolePluginManifest[];
}

export default function Sidebar({ selectedKey, plugins = [] }: SidebarProps) {
  const keyToPath = useMemo(
    () => ({
      ...BASE_KEY_TO_PATH,
      ...Object.fromEntries(
        plugins.map((p) => [
          p.path.replace(/^\//, "").replace(/\//g, "-"),
          p.path,
        ])
      ),
    }),
    [plugins]
  );
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [openKeys, setOpenKeys] = useState<string[]>([
    "chat-group",
    "control-group",
    "agent-group",
    "explore-group",
    "settings-group",
  ]);
  const [version, setVersion] = useState<string>("");

  useEffect(() => {
    api
      .getVersion()
      .then((res) => setVersion(res?.version ?? ""))
      .catch(() => {});
  }, []);

  const pluginMenuItems: MenuProps["items"] =
    plugins.length > 0
      ? plugins.map((p) => ({
          key: p.path.replace(/^\//, "").replace(/\//g, "-"),
          label: p.label,
          icon: PLUGIN_ICON_MAP[p.icon] ?? <Plug size={16} />,
        }))
      : [
          { key: "warroom", label: "War Room", icon: <Radio size={16} /> },
          { key: "analytics", label: "Analytics", icon: <BarChart3 size={16} /> },
          {
            key: "leaderboard",
            label: "Leaderboard",
            icon: <Trophy size={16} />,
          },
        ];

  const menuItems: MenuProps["items"] = [
    {
      key: "dashboard",
      label: t("nav.dashboard"),
      icon: <LayoutDashboard size={16} />,
    },
    ...pluginMenuItems,
    {
      key: "chat-group",
      label: t("nav.chat"),
      icon: <MessageSquare size={16} />,
      children: [
        {
          key: "chat",
          label: t("nav.chat"),
          icon: <MessageCircle size={16} />,
        },
      ],
    },
    {
      key: "control-group",
      label: t("nav.control"),
      icon: <Radio size={16} />,
      children: [
        {
          key: "channels",
          label: t("nav.channels"),
          icon: <Wifi size={16} />,
        },
        {
          key: "sessions",
          label: t("nav.sessions"),
          icon: <UsersRound size={16} />,
        },
        {
          key: "cron-jobs",
          label: t("nav.cronJobs"),
          icon: <CalendarClock size={16} />,
        },
        {
          key: "monitoring",
          label: "Monitoring",
          icon: <Eye size={16} />,
        },
      ],
    },
    {
      key: "agent-group",
      label: t("nav.agent"),
      icon: <Zap size={16} />,
      children: [
        {
          key: "workspace",
          label: t("nav.workspace"),
          icon: <Briefcase size={16} />,
        },
        {
          key: "skills",
          label: t("nav.skills"),
          icon: <Sparkles size={16} />,
        },
        {
          key: "mcp",
          label: t("nav.mcp"),
          icon: <Plug size={16} />,
        },
        {
          key: "agent-config",
          label: t("nav.agentConfig"),
          icon: <Settings size={16} />,
        },
        {
          key: "memory",
          label: "Memory",
          icon: <Cpu size={16} />,
        },
        {
          key: "team-builder",
          label: "Team Builder",
          icon: <UsersRound size={16} />,
        },
        // Replay and Terminal hidden until UI/backend are ready
      ],
    },
    {
      key: "explore-group",
      label: "Explore",
      icon: <Globe size={16} />,
      children: [
        {
          key: "marketplace",
          label: "Marketplace",
          icon: <Store size={16} />,
        },
        {
          key: "agentverse",
          label: "AgentVerse",
          icon: <Bot size={16} />,
        },
        {
          key: "swarm",
          label: "Swarm",
          icon: <Globe size={16} />,
        },
        {
          key: "credits",
          label: "Credits",
          icon: <Zap size={16} />,
        },
      ],
    },
    {
      key: "settings-group",
      label: t("nav.settings"),
      icon: <Cpu size={16} />,
      children: [
        {
          key: "models",
          label: t("nav.models"),
          icon: <Box size={16} />,
        },
        {
          key: "hardware",
          label: "Hardware Advisor",
          icon: <HardDrive size={16} />,
        },
        {
          key: "environments",
          label: t("nav.environments"),
          icon: <Globe size={16} />,
        },
        {
          key: "security",
          label: "Security",
          icon: <Shield size={16} />,
        },
        {
          key: "privacy",
          label: "Privacy",
          icon: <Eye size={16} />,
        },
        {
          key: "appearance",
          label: "Appearance",
          icon: <Palette size={16} />,
        },
      ],
    },
  ];

  return (
    <Sider
      width={260}
      style={{
        background: "var(--pb-bg-elevated)",
        borderRight: "1px solid var(--pb-border)",
      }}
    >
      <div
        style={{
          minHeight: 64,
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          flexWrap: "wrap",
          padding: "12px 12px",
          fontWeight: 600,
          gap: 8,
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            maxWidth: "100%",
            minHeight: 48,
            padding: "6px 10px",
            backgroundColor: "rgb(255, 255, 255)",
            border: "1px solid rgba(0, 0, 0, 0.12)",
            borderRadius: 8,
            boxShadow: "0px 4px 12px 0px rgba(0, 0, 0, 0.15)",
            overflow: "hidden",
            boxSizing: "border-box",
          }}
        >
          <img
            src="/logo.png"
            alt="ProwlrBot"
            style={{
              maxWidth: "100%",
              width: "auto",
              height: "36px",
              display: "block",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </div>
        {version && (
          <span
            style={{
              fontSize: 11,
              color: "var(--pb-text-tertiary)",
              fontWeight: 400,
              lineHeight: 1,
            }}
          >
            v{version}
          </span>
        )}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        openKeys={openKeys}
        onOpenChange={(keys) => setOpenKeys(keys as string[])}
        onClick={(info: { key: string | number }) => {
          const key = String(info.key);
          const path = keyToPath[key];
          if (path) {
            navigate(path);
          }
        }}
        items={menuItems}
      />
    </Sider>
  );
}
