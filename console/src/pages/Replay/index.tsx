import { useState, useEffect, useCallback } from "react";
import { Button, Empty, Tag } from "antd";
import {
  PlayCircleOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";
import { request } from "../../api/request";

interface ReplaySession {
  session_id: string;
  agent_name: string;
  start_time: string;
  end_time?: string;
  message_count: number;
  status: string;
}

export default function ReplayPage() {
  const [sessions, setSessions] = useState<ReplaySession[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await request<ReplaySession[]>("/replay/sessions").catch(
        () => null,
      );
      if (Array.isArray(data)) {
        setSessions(data);
      }
    } catch {
      // API not available yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return (
    <div style={{ padding: 24 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <div>
          <h3 style={{ margin: 0 }}>
            <PlayCircleOutlined style={{ marginRight: 8 }} />
            Replay
          </h3>
          <p style={{ color: "#888", fontSize: 13, marginTop: 4, marginBottom: 0 }}>
            Replay past agent sessions to review decisions, debug issues, or
            learn from agent behavior.
          </p>
        </div>
        <Button icon={<ReloadOutlined />} onClick={fetchSessions} loading={loading}>
          Refresh
        </Button>
      </div>

      {sessions.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <span>
              No replay sessions available yet.
              <br />
              Sessions will appear here after agent conversations are recorded.
            </span>
          }
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {sessions.map((session) => (
            <div
              key={session.session_id}
              style={{
                border: "1px solid #f0f0f0",
                borderRadius: 8,
                padding: 16,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <div style={{ fontWeight: 500 }}>{session.agent_name}</div>
                <div style={{ color: "#888", fontSize: 12, marginTop: 4 }}>
                  <ClockCircleOutlined style={{ marginRight: 4 }} />
                  {new Date(session.start_time).toLocaleString()}
                  {" \u2014 "}
                  {session.message_count} messages
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Tag
                  color={session.status === "completed" ? "green" : "blue"}
                >
                  {session.status}
                </Tag>
                <Button
                  type="primary"
                  size="small"
                  icon={<PlayCircleOutlined />}
                >
                  Replay
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
