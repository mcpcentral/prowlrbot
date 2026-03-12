import { Layout } from "antd";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useTranslation } from "react-i18next";

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
          // i18n keys start with "nav.", raw strings don't
          return label.startsWith("nav.") ? t(label) : label;
        })()}
      </span>
      <LanguageSwitcher />
    </AntHeader>
  );
}
