import { Layout, Menu, type MenuProps } from "antd";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api";
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

const keyToPath: Record<string, string> = {
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
};

interface SidebarProps {
  selectedKey: string;
}

export default function Sidebar({ selectedKey }: SidebarProps) {
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

  const menuItems: MenuProps["items"] = [
    {
      key: "dashboard",
      label: t("nav.dashboard"),
      icon: <LayoutDashboard size={16} />,
    },
    {
      key: "warroom",
      label: "War Room",
      icon: <Radio size={16} />,
    },
    {
      key: "analytics",
      label: "Analytics",
      icon: <BarChart3 size={16} />,
    },
    {
      key: "leaderboard",
      label: "Leaderboard",
      icon: <Trophy size={16} />,
    },
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
        {
          key: "replay",
          label: "Replay",
          icon: <Box size={16} />,
        },
        {
          key: "terminal",
          label: "Terminal",
          icon: <Cpu size={16} />,
        },
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
          height: 64,
          display: "flex",
          alignItems: "flex-end",
          padding: "0 24px 10px",
          fontWeight: 600,
          gap: 8,
        }}
      >
        <img
          src="/logo.png"
          alt="ProwlrBot"
          style={{ height: 32, width: "auto" }}
        />
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
