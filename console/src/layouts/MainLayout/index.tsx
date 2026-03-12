import { Layout } from "antd";
import { useEffect } from "react";
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../Sidebar";
import Header from "../Header";
import ConsoleCronBubble from "../../components/ConsoleCronBubble";
import Dashboard from "../../pages/Dashboard";
import Chat from "../../pages/Chat";
import ChannelsPage from "../../pages/Control/Channels";
import SessionsPage from "../../pages/Control/Sessions";
import CronJobsPage from "../../pages/Control/CronJobs";
import HeartbeatPage from "../../pages/Control/Heartbeat";
import AgentConfigPage from "../../pages/Agent/Config";
import SkillsPage from "../../pages/Agent/Skills";
import WorkspacePage from "../../pages/Agent/Workspace";
import MCPPage from "../../pages/Agent/MCP";
import ModelsPage from "../../pages/Settings/Models";
import EnvironmentsPage from "../../pages/Settings/Environments";
import MarketplacePage from "../../pages/Marketplace";
import AgentVersePage from "../../pages/AgentVerse";
import GamificationPage from "../../pages/Gamification";
import LeaderboardPage from "../../pages/Leaderboard";
import SecurityPage from "../../pages/Settings/Security";
import PrivacyPage from "../../pages/Settings/Privacy";
import TemplatesPage from "../../pages/Settings/Templates";
import AppearancePage from "../../pages/Settings/Appearance";
import OnboardingPage from "../../pages/Settings/Onboarding";
import WarRoomPage from "../../pages/WarRoom";
import MonitoringPage from "../../pages/Monitoring";
import MemoryPage from "../../pages/Memory";
import SwarmPage from "../../pages/Swarm";
import SoulEditorPage from "../../pages/Agent/SoulEditor";
import TeamBuilderPage from "../../pages/Agent/TeamBuilder";
import ResearchPage from "../../pages/Research";
import ReplayPage from "../../pages/Replay";
import ExternalAgentsPage from "../../pages/ExternalAgents";

const { Content } = Layout;

const pathToKey: Record<string, string> = {
  "/dashboard": "dashboard",
  "/chat": "chat",
  "/channels": "channels",
  "/sessions": "sessions",
  "/cron-jobs": "cron-jobs",
  "/heartbeat": "heartbeat",
  "/skills": "skills",
  "/mcp": "mcp",
  "/workspace": "workspace",
  "/agents": "agents",
  "/models": "models",
  "/environments": "environments",
  "/agent-config": "agent-config",
  "/marketplace": "marketplace",
  "/agentverse": "agentverse",
  "/gamification": "gamification",
  "/leaderboard": "leaderboard",
  "/security": "security",
  "/privacy": "privacy",
  "/appearance": "appearance",
  "/templates": "templates",
  "/research": "research",
  "/replay": "replay",
  "/external-agents": "external-agents",
  "/onboarding": "onboarding",
  "/warroom": "warroom",
  "/monitoring": "monitoring",
  "/memory": "memory",
  "/swarm": "swarm",
  "/soul-editor": "soul-editor",
  "/team-builder": "team-builder",
};

export default function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;
  const selectedKey = pathToKey[currentPath] || "dashboard";

  useEffect(() => {
    if (currentPath === "/") {
      navigate("/dashboard", { replace: true });
    }
  }, [currentPath, navigate]);

  return (
    <Layout style={{ height: "100vh" }}>
      <Sidebar selectedKey={selectedKey} />
      <Layout>
        <Header selectedKey={selectedKey} />
        <Content className="page-container">
          <ConsoleCronBubble />
          <div className="page-content">
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/channels" element={<ChannelsPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
              <Route path="/cron-jobs" element={<CronJobsPage />} />
              <Route path="/heartbeat" element={<HeartbeatPage />} />
              <Route path="/skills" element={<SkillsPage />} />
              <Route path="/mcp" element={<MCPPage />} />
              <Route path="/workspace" element={<WorkspacePage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/environments" element={<EnvironmentsPage />} />
              <Route path="/agent-config" element={<AgentConfigPage />} />
              <Route path="/marketplace" element={<MarketplacePage />} />
              <Route path="/agentverse" element={<AgentVersePage />} />
              <Route path="/gamification" element={<GamificationPage />} />
              <Route path="/leaderboard" element={<LeaderboardPage />} />
              <Route path="/security" element={<SecurityPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/appearance" element={<AppearancePage />} />
              <Route path="/templates" element={<TemplatesPage />} />
              <Route path="/onboarding" element={<OnboardingPage />} />
              <Route path="/warroom" element={<WarRoomPage />} />
              <Route path="/monitoring" element={<MonitoringPage />} />
              <Route path="/memory" element={<MemoryPage />} />
              <Route path="/swarm" element={<SwarmPage />} />
              <Route path="/soul-editor" element={<SoulEditorPage />} />
              <Route path="/team-builder" element={<TeamBuilderPage />} />
              <Route path="/research" element={<ResearchPage />} />
              <Route path="/replay" element={<ReplayPage />} />
              <Route path="/external-agents" element={<ExternalAgentsPage />} />
              <Route path="/" element={<Dashboard />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
