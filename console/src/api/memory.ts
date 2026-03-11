import { request } from "./request";

export interface MemoryEntry {
  id: string;
  agent_id: string;
  topic: string;
  summary: string;
  tier: "short" | "medium" | "long";
  access_count: number;
  importance: number;
  created_at: string;
  last_accessed: string;
}

export function searchMemory(
  agentId: string,
  query: string,
): Promise<MemoryEntry[]> {
  return request<MemoryEntry[]>(
    `/memory/search?agent_id=${encodeURIComponent(agentId)}&q=${encodeURIComponent(query)}`,
  );
}

export function getAgentMemory(
  agentId: string,
  tier?: string,
): Promise<MemoryEntry[]> {
  const params = new URLSearchParams({ agent_id: agentId });
  if (tier) params.set("tier", tier);
  return request<MemoryEntry[]>(`/memory?${params}`);
}

export function promoteMemory(entryId: string): Promise<void> {
  return request<void>(`/memory/${entryId}/promote`, { method: "POST" });
}
