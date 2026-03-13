import { Avatar, Dropdown, Layout, Space, Tag } from "antd";
import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";

const { Header: AntHeader } = Layout;

const keyToLabel: Record<string, string> = {
  dashboard: "nav.dashboard",
  chat: "nav.chat",
  channels: "nav.channels",
  sessions: "nav.sessions",
  "cron-jobs": "nav.cronJobs",
  skills: "nav.skills",
  mcp: "nav.mcp",
  "agent-config": "nav.agentConfig",
  workspace: "nav.workspace",
  models: "nav.models",
  environments: "nav.environments",
  marketplace: "Marketplace",
  agentverse: "AgentVerse",
  security: "Security",
  privacy: "Privacy",
  appearance: "Appearance",
  warroom: "War Room",
  monitoring: "Monitoring",
  memory: "Memory",
  swarm: "Swarm",
  "team-builder": "Team Builder",
};

interface HeaderProps {
  selectedKey: string;
}

export default function Header({ selectedKey }: HeaderProps) {
  const { t } = useTranslation();
  const { user, onLogout } = useAuth();

  const userMenuItems = [
    {
      key: "role",
      label: (
        <Space>
          <span>{user?.username}</span>
          <Tag color="blue">{user?.role}</Tag>
        </Space>
      ),
      disabled: true,
    },
    { type: "divider" as const },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "Sign Out",
      onClick: onLogout,
    },
  ];

  return (
    <AntHeader
      style={{
        height: 64,
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "var(--pb-bg-elevated)",
        borderBottom: "1px solid var(--pb-border)",
      }}
    >
      <span style={{ fontSize: 18, fontWeight: 500, color: "var(--pb-text-primary)" }}>
        {(() => {
          const label = keyToLabel[selectedKey];
          if (!label) return t("nav.dashboard");
          return label.startsWith("nav.") ? t(label) : label;
        })()}
      </span>
      <Space size="middle">
        <LanguageSwitcher />
        {user && (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={["click"]}>
            <Avatar
              icon={<UserOutlined />}
              style={{ cursor: "pointer", backgroundColor: "var(--pb-brand-primary)" }}
            />
          </Dropdown>
        )}
      </Space>
    </AntHeader>
  );
}
