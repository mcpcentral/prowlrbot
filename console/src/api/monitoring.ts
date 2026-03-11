import { request } from "./request";

export interface Monitor {
  id: string;
  type: "web" | "api";
  url: string;
  interval_minutes: number;
  last_checked: string;
  status: "ok" | "changed" | "error" | "unknown";
  last_diff?: string;
}

export interface MonitorCheck {
  id: string;
  monitor_id: string;
  status: string;
  checked_at: string;
  diff?: string;
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
