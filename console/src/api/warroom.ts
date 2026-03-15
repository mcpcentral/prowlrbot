import { getApiTokenAsync } from "./config";
import { request } from "./request";

export interface Agent {
  agent_id: string;
  name: string;
  capabilities: string[];
  status: "idle" | "working" | "disconnected";
  current_task_id: string | null;
  last_heartbeat: string;
  registered_at: string;
}

export interface Task {
  task_id: string;
  title: string;
  description: string;
  status: "pending" | "claimed" | "in_progress" | "done" | "failed";
  priority: string;
  owner_agent_id: string | null;
  owner_name: string | null;
  file_scopes: string[];
  blocked_by: string[];
  progress_note: string;
  created_at: string;
  claimed_at: string | null;
  completed_at: string | null;
}

export interface WarRoomEvent {
  event_id: string;
  type: string;
  agent_id: string | null;
  task_id: string | null;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface Finding {
  key: string;
  agent_id: string;
  value: string;
  updated_at: string;
}

export interface FileLock {
  file_path: string;
  agent_id: string;
  task_id: string;
  lock_token: string;
  acquired_at: string;
}

export const warroom = {
  agents: () => request<Agent[]>("/warroom/agents"),
  board: (status?: string) =>
    request<Task[]>(`/warroom/board${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  events: (limit = 50) =>
    request<WarRoomEvent[]>(`/warroom/events?limit=${limit}`),
  context: () => request<Finding[]>("/warroom/context"),
  conflicts: () => request<FileLock[]>("/warroom/conflicts"),
  health: () => request<{ status: string; agents: number; tasks: number }>("/warroom/health"),
};

/** Bridge may send flat { type, timestamp, agent_id?, task_id?, ... } without event_id or nested payload. */
export async function connectWarRoomWS(
  onEvent: (event: WarRoomEvent | Record<string, unknown>) => void,
  onStatus: (connected: boolean) => void,
): Promise<() => void> {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const token =
    (import.meta.env.VITE_WARROOM_TOKEN as string | undefined) || (await getApiTokenAsync());
  const wsUrl = `${protocol}//${window.location.host}/ws/warroom${
    token ? `?token=${encodeURIComponent(token)}` : ""
  }`;
  let ws: WebSocket | null = null;
  let pingTimer: ReturnType<typeof setInterval> | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectDelay = 1000;
  let disposed = false;

  function connect() {
    if (disposed) return;
    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
      onStatus(true);
      reconnectDelay = 1000; // Reset backoff on success
      pingTimer = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) ws.send("ping");
      }, 25000);
    };
    ws.onclose = () => {
      onStatus(false);
      if (pingTimer) clearInterval(pingTimer);
      if (!disposed) {
        reconnectTimer = setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30000); // Exponential backoff
      }
    };
    ws.onerror = () => {
      ws?.close();
    };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type && data.type !== "keepalive") {
          onEvent(data);
        }
      } catch {
        // Ignore non-JSON messages (like "pong")
      }
    };
  }

  connect();

  return () => {
    disposed = true;
    if (pingTimer) clearInterval(pingTimer);
    if (reconnectTimer) clearTimeout(reconnectTimer);
    ws?.close();
  };
}
