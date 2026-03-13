import { useEffect, useRef, useState } from "react";

export interface LeaderboardEntry {
  entity_id: string;
  entity_type: string;
  total_xp: number;
  level: number;
}

export function useLeaderboard(entityType: "agent" | "user" = "agent") {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const refresh = () => {
    fetch(`/api/gamification/leaderboard?entity_type=${entityType}&limit=20`)
      .then((r) => r.json())
      .then((data) => {
        setEntries(data);
        setLastUpdate(new Date());
      })
      .catch(() => {/* best-effort */});
  };

  useEffect(() => {
    // Initial load
    refresh();

    // Connect to WebSocket for live leaderboard_update events
    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard?session_id=leaderboard`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          // Handle both {type: "leaderboard_update"} and nested formats
          if (
            msg.type === "leaderboard_update" ||
            msg.event === "leaderboard_update" ||
            (msg.data && msg.data.type === "leaderboard_update")
          ) {
            refresh();
          }
        } catch {
          // ignore non-JSON
        }
      };

      ws.onerror = () => {/* silent */};

      return () => ws.close();
    } catch {
      return () => {};
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType]);

  return { entries, lastUpdate, refresh };
}
