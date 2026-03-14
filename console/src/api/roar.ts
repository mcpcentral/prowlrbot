/**
 * ROAR Protocol (Layer 5 Stream) — StreamEvent types for real-time agent activity.
 * @see docs/protocols/ROAR-STREAM.md
 */

export type RoarStreamEventType =
  | "tool_call"
  | "mcp_request"
  | "reasoning"
  | "task_update"
  | "monitor_alert"
  | "agent_status"
  | "checkpoint"
  | "world_update";

export interface RoarStreamEvent {
  type: RoarStreamEventType;
  source: string;
  session_id: string;
  data: Record<string, unknown>;
  timestamp: number;
}

import { getRoarEventsUrl } from "./config";

/**
 * Subscribe to ROAR SSE stream. Call with onEvent and optionally onStatus.
 * Returns a disconnect function. Uses same-origin /roar/events (proxy to backend).
 */
export function subscribeRoarStream(
  onEvent: (event: RoarStreamEvent) => void,
  onStatus?: (connected: boolean) => void,
): () => void {
  const url = getRoarEventsUrl();
  let eventSource: EventSource | null = null;
  let disposed = false;

  function connect() {
    if (disposed) return;
    try {
      eventSource = new EventSource(url);
      eventSource.onopen = () => onStatus?.(true);
      eventSource.onerror = () => {
        onStatus?.(false);
        eventSource?.close();
        if (!disposed) setTimeout(connect, 5000);
      };
      eventSource.addEventListener("connected", () => {});
      eventSource.addEventListener("tool_call", (e) => forward(e));
      eventSource.addEventListener("mcp_request", (e) => forward(e));
      eventSource.addEventListener("reasoning", (e) => forward(e));
      eventSource.addEventListener("task_update", (e) => forward(e));
      eventSource.addEventListener("monitor_alert", (e) => forward(e));
      eventSource.addEventListener("agent_status", (e) => forward(e));
      eventSource.addEventListener("checkpoint", (e) => forward(e));
      eventSource.addEventListener("world_update", (e) => forward(e));
    } catch {
      onStatus?.(false);
    }
  }

  function forward(e: MessageEvent) {
    try {
      const data = JSON.parse(e.data ?? "{}");
      const ev: RoarStreamEvent = {
        type: (e.type as RoarStreamEventType) || "task_update",
        source: data.source ?? "",
        session_id: data.session_id ?? "",
        data: data.data ?? {},
        timestamp: data.timestamp ?? Date.now() / 1000,
      };
      onEvent(ev);
    } catch {
      // ignore parse errors
    }
  }

  connect();

  return () => {
    disposed = true;
    eventSource?.close();
  };
}
