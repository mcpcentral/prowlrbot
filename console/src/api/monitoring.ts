import { request } from "./request";

export interface Monitor {
  id: string;
  type: "web" | "api";
  url: string;
  interval_minutes: number;
  enabled?: boolean;
  last_checked: string | null;
  status: "ok" | "changed" | "error" | "unknown";
  last_diff?: string;
}

/** Backend returns { monitor_name?, checked_at, content_length? } per check. */
export interface MonitorCheck {
  monitor_name?: string;
  checked_at: string;
  content_length?: number;
}

export interface CreateMonitorRequest {
  url: string;
  type: "web" | "api";
  interval_minutes: number;
}

export function getMonitors(): Promise<Monitor[]> {
  return request<Monitor[]>("/monitors");
}

export function getMonitorHistory(
  monitorId: string,
): Promise<MonitorCheck[]> {
  return request<MonitorCheck[]>(`/monitors/${monitorId}/history`);
}

export function createMonitor(
  config: CreateMonitorRequest,
): Promise<Monitor> {
  return request<Monitor>("/monitors", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export function deleteMonitor(monitorId: string): Promise<void> {
  return request<void>(`/monitors/${monitorId}`, {
    method: "DELETE",
  });
}
