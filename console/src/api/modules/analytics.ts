import { request } from "../request";

export interface UsageSummary {
  total_tokens: number;
  total_cost: number;
  total_queries: number;
  avg_latency_ms: number;
}

export interface ModelStats {
  input_tokens: number;
  output_tokens: number;
  total_cost: number;
  query_count: number;
  avg_latency_ms: number;
}

export interface CostDataPoint {
  date: string;
  cost: number;
  tokens: number;
  queries: number;
}

export interface UsageStat {
  id: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  latency_ms: number;
  timestamp: string;
}

export function getAnalyticsSummary(period: "day" | "week" | "month" | "all" = "day") {
  return request<UsageSummary>(`/analytics/summary?period=${period}`);
}

export function getModelBreakdown() {
  return request<Record<string, ModelStats>>("/analytics/models");
}

export function getCostOverTime(days = 7) {
  return request<CostDataPoint[]>(`/analytics/cost-over-time?days=${days}`);
}

export function getRecentUsage(limit = 50) {
  return request<UsageStat[]>(`/analytics/recent?limit=${limit}`);
}
