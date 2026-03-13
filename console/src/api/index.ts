export * from "./types";

export { request } from "./request";

export { getApiUrl, getApiToken } from "./config";

import { rootApi } from "./modules/root";
import { channelApi } from "./modules/channel";
import { heartbeatApi } from "./modules/heartbeat";
import { cronJobApi } from "./modules/cronjob";
import { chatApi, sessionApi } from "./modules/chat";
import { envApi } from "./modules/env";
import { providerApi } from "./modules/provider";
import { skillApi } from "./modules/skill";
import { agentApi } from "./modules/agent";
import { workspaceApi } from "./modules/workspace";
import { localModelApi } from "./modules/localModel";
import { ollamaModelApi } from "./modules/ollamaModel";
import { mcpApi } from "./modules/mcp";

// New module re-exports
export * from "./modules/marketplace";
export * from "./modules/agentverse";
export * from "./modules/gamification";
export * from "./modules/autonomy";
export * from "./modules/notifications";
export * from "./modules/templates";
export * from "./modules/research";
export * from "./modules/replay";
export * from "./modules/health";
export * from "./modules/leaderboard";
export * from "./modules/externalAgents";
export * from "./modules/analytics";
export * from "./modules/credits";

export const api = {
  // Root
  ...rootApi,

  // Channels
  ...channelApi,

  // Heartbeat
  ...heartbeatApi,

  // Cron Jobs
  ...cronJobApi,

  // Chats
  ...chatApi,

  // Sessions（Legacy aliases）
  ...sessionApi,

  // Environment Variables
  ...envApi,

  // Providers
  ...providerApi,

  // Agent
  ...agentApi,

  // Skills
  ...skillApi,

  // Workspace
  ...workspaceApi,

  // Local Models
  ...localModelApi,

  // Ollama Models
  ...ollamaModelApi,

  // MCP Clients
  ...mcpApi,
};

export default api;
